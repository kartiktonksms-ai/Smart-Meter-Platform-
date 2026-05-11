from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    meters = db.relationship('Meter', backref='owner', lazy=True)

class Meter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meter_number = db.Column(db.String(50), unique=True, nullable=False)
    type = db.Column(db.String(20), nullable=False) # e.g., 'Residential', 'Commercial'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    readings = db.relationship('Reading', backref='meter', lazy=True, cascade="all, delete-orphan")
    bills = db.relationship('Bill', backref='meter', lazy=True, cascade="all, delete-orphan")

class Reading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meter_id = db.Column(db.Integer, db.ForeignKey('meter.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    consumption_kwh = db.Column(db.Float, nullable=False) # Actual reading value for that hour

class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meter_id = db.Column(db.Integer, db.ForeignKey('meter.id'), nullable=False)
    billing_period_start = db.Column(db.DateTime, nullable=False)
    billing_period_end = db.Column(db.DateTime, nullable=False)
    total_consumption_kwh = db.Column(db.Float, nullable=False)
    amount_due = db.Column(db.Float, nullable=False)
    is_paid = db.Column(db.Boolean, default=False)
    details = db.Column(db.Text) # JSON string of tier breakdown
