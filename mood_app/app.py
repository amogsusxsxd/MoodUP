from flask import Flask, render_template, request, jsonify
from datetime import datetime
import json
import os

app = Flask(__name__)

# Пути к файлам с данными
MOOD_DATA_FILE = 'mood_data.json'
JOURNAL_DATA_FILE = 'journal_data.json'
NOTIFICATIONS_FILE = 'notifications_settings.json'

# Инициализация файлов данных, если их нет
if not os.path.exists(MOOD_DATA_FILE):
    with open(MOOD_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f)

if not os.path.exists(JOURNAL_DATA_FILE):
    with open(JOURNAL_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f)

if not os.path.exists(NOTIFICATIONS_FILE):
    with open(NOTIFICATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            'enabled': True,
            'times': ['09:00', '12:00', '18:00'],
            'frequency': 3,
            'theme': 'positive',
            'savedAt': datetime.now().isoformat()
        }, f)

def load_mood_data():
    with open(MOOD_DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_mood_data(data):
    with open(MOOD_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_journal_data():
    with open(JOURNAL_DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_journal_data(data):
    with open(JOURNAL_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_notifications_settings():
    with open(NOTIFICATIONS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_notifications_settings(data):
    with open(NOTIFICATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/save', methods=['POST'])
def save():
    data = request.json
    mood = data.get('mood')
    
    if mood not in ['happy', 'sad', 'angry', 'calm']:
        return jsonify({'message': 'Неверное настроение'}), 400
    
    records = load_mood_data()
    new_record = {
        'stamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'mood': mood
    }
    records.append(new_record)
    save_mood_data(records)
    
    messages = {
        'happy': 'Счастье — это когда тебя понимают, большое счастье — это когда тебя любят, настоящее счастье — это когда любишь ты',
        'sad': 'Когда тебе плохо — прислушайся к природе. Тишина мира успокаивает лучше, чем миллионы ненужных слов',
        'angry': 'Когда поднимается гнев, думай о последствиях',
        'calm': 'То, что вы можете воспринимать спокойно, больше не управляет вами'
    }
    
    return jsonify({'message': messages[mood]})

@app.route('/calendar')
def calendar():
    records = load_mood_data()
    return render_template('calendar.html', records=records)

@app.route('/journal')
def journal():
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('journal.html', today=today)

@app.route('/save_journal', methods=['POST'])
def save_journal():
    data = request.json
    date = data.get('date')
    text = data.get('text')
    
    if not date or not text:
        return jsonify({
            'success': False,
            'message': 'Дата и текст обязательны'
        }), 400
    
    journal_records = load_journal_data()
    
    # Добавляем новую запись
    new_entry = {
        'date': date,
        'text': text,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    journal_records.append(new_entry)
    
    # Сохраняем обратно
    save_journal_data(journal_records)
    
    return jsonify({
        'success': True,
        'message': 'Запись успешно сохранена!'
    })

@app.route('/notifications')
def notifications():
    settings = load_notifications_settings()
    return render_template('notifications.html', settings=settings)

@app.route('/save_notifications', methods=['POST'])
def save_notifications():
    data = request.json
    
    # Сохраняем настройки
    save_notifications_settings(data)
    
    return jsonify({
        'success': True,
        'message': 'Настройки уведомлений сохранены!'
    })

@app.route('/statistics')
def statistics():
    records = load_mood_data()
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('statistics.html', records=records, today=today)

@app.route('/api/statistics')
def api_statistics():
    records = load_mood_data()
    
    # Параметры фильтрации
    period = request.args.get('period', 'week')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    # Фильтрация записей по дате
    filtered_records = []
    for record in records:
        record_date_str = record['stamp'].split()[0]
        
        try:
            record_date = datetime.strptime(record_date_str, '%Y-%m-%d')
        except ValueError:
            continue
        
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                if record_date < start:
                    continue
            except ValueError:
                pass
        
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            if record_date > end:
                continue
        except ValueError:
            pass
            
        filtered_records.append(record)
    
    # Анализ данных
    mood_counts = {'happy': 0, 'calm': 0, 'sad': 0, 'angry': 0}
    daily_data = {}
    
    for record in filtered_records:
        mood = record['mood']
        date = record['stamp'].split()[0]
        
        mood_counts[mood] += 1
        
        if date not in daily_data:
            daily_data[date] = {'happy': 0, 'calm': 0, 'sad': 0, 'angry': 0}
        daily_data[date][mood] += 1
    
    total = sum(mood_counts.values())
    percentages = {}
    for mood, count in mood_counts.items():
        percentages[mood] = round((count / total * 100), 2) if total > 0 else 0
    
    # Преобразование daily_data в массив
    daily_array = []
    for date, counts in sorted(daily_data.items()):
        if sum(counts.values()) > 0:
            dominant_mood = max(counts.items(), key=lambda x: x[1])[0]
            daily_array.append({
                'date': date,
                'mood': dominant_mood,
                'count': sum(counts.values())
            })
    
    return jsonify({
        'success': True,
        'statistics': {
            'counts': mood_counts,
            'percentages': percentages,
            'total': total,
            'daily_data': daily_array,
            'period': period
        }
    })

if __name__ == '__main__':
    app.run(debug=True, port=5001)