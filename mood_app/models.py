from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Record(db.Model):
    id    = db.Column(db.Integer, primary_key=True)
    mood  = db.Column(db.String(20), nullable=False)   # happy, sad, angry, calm
    stamp = db.Column(db.Date, default=datetime.utcnow)