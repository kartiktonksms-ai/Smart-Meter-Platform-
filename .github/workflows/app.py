from flask import Flask, render_template, jsonify, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Meter, Reading, Bill
from simulator import generate_mock_data, generate_mock_data_for_meter, calculate_tier_pricing
from datetime import datetime, timedelta
import os
import json
import random

app = Flask(__name__)
# Secret key needed for sessions
app.config['SECRET_KEY'] = 'your_secret_key_here'
# Use an absolute path for the sqlite DB
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'platform.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Authentication Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
            
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        address = request.form.get('address')
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists', 'error')
            return redirect(url_for('signup'))
            
        new_user = User(
            email=email, 
            name=name, 
            password_hash=generate_password_hash(password, method='pbkdf2:sha256'),
            address=address
        )
        db.session.add(new_user)
        db.session.commit()
        
        # Create a smart meter for the new user
        meter_number = f"SM-{random.randint(100000000, 999999999)}"
        meter = Meter(meter_number=meter_number, type="Residential", user_id=new_user.id)
        db.session.add(meter)
        db.session.commit()
        
        # Generate initial history so the UI has data right away.
        generate_mock_data_for_meter(meter.id, new_user.id)
        
        return redirect(url_for('login'))
        
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- App Routes ---
@app.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/analytics')
@login_required
def analytics():
    return render_template('analytics.html')

@app.route('/billing')
@login_required
def billing():
    return render_template('billing.html')

# API Endpoints
@app.route('/api/summary')
@login_required
def api_summary():
    user = current_user
    meter = Meter.query.filter_by(user_id=user.id).first()
    if not meter:
        return jsonify({"error": "No meter found for this user"}), 404
    
    # Calculate real-time consumption for the last 30 days
    start_time = datetime.now() - timedelta(days=30)
    readings = Reading.query.filter(
        Reading.meter_id == meter.id,
        Reading.timestamp >= start_time
    ).all()
    
    total_consumption = sum(r.consumption_kwh for r in readings)
    current_bill, _ = calculate_tier_pricing(total_consumption)
    
    # Bill summary and alerts
    bills = Bill.query.filter_by(meter_id=meter.id).order_by(Bill.billing_period_end.desc()).all()
    paid_count = sum(1 for b in bills if b.is_paid)
    pending_count = sum(1 for b in bills if not b.is_paid)
    
    alerts = []
    now = datetime.now()
    for b in bills:
        if not b.is_paid:
            # Assume due date is 15 days after billing_period_end
            due_date = b.billing_period_end + timedelta(days=15)
            days_left = (due_date - now).days
            if 0 <= days_left <= 5:
                alerts.append(f"Bill for {b.billing_period_end.strftime('%b %Y')} is due in {days_left} days! (₹{b.amount_due:.2f})")
            elif days_left < 0:
                alerts.append(f"Bill for {b.billing_period_end.strftime('%b %Y')} is OVERDUE by {abs(days_left)} days! (₹{b.amount_due:.2f})")

    recent_bills = []
    for b in bills[:3]:
        recent_bills.append({
            "period": f"{b.billing_period_start.strftime('%b %d')} - {b.billing_period_end.strftime('%b %d')}",
            "amount": b.amount_due,
            "status": "Paid" if b.is_paid else "Pending"
        })
    
    return jsonify({
        "user_name": user.name,
        "meter_number": meter.meter_number,
        "total_consumption": round(total_consumption, 2),
        "current_bill": round(current_bill, 2),
        "paid_count": paid_count,
        "pending_count": pending_count,
        "alerts": alerts,
        "recent_bills": recent_bills
    })

@app.route('/api/daily_readings')
@login_required
def api_daily_readings():
    # Get total reading per day for the last 30 days
    meter = Meter.query.filter_by(user_id=current_user.id).first()
    if not meter:
        return jsonify({"labels": [], "data": []})
    
    readings = Reading.query.filter_by(meter_id=meter.id).all()
    
    daily_sum = {}
    for r in readings:
        date_str = r.timestamp.strftime('%Y-%m-%d')
        if date_str not in daily_sum:
            daily_sum[date_str] = 0
        daily_sum[date_str] += r.consumption_kwh
        
    # Sort by date
    sorted_dates = sorted(daily_sum.keys())
    
    labels = sorted_dates
    values = [round(daily_sum[d], 2) for d in sorted_dates]
    
    return jsonify({"labels": labels, "data": values})
    
@app.route('/api/hourly_readings')
@login_required
def api_hourly_readings():
    # Last 24 hours
    meter = Meter.query.filter_by(user_id=current_user.id).first()
    if not meter:
        return jsonify({"labels": [], "data": []})
    
    last_reading = Reading.query.filter_by(meter_id=meter.id).order_by(Reading.timestamp.desc()).first()
    if not last_reading:
         return jsonify({"labels": [], "data": []})
         
    start_time = last_reading.timestamp - timedelta(hours=24)
    readings = Reading.query.filter(
        Reading.meter_id == meter.id,
        Reading.timestamp >= start_time
    ).order_by(Reading.timestamp.asc()).all()
    
    labels = [r.timestamp.strftime('%H:%M') for r in readings]
    values = [r.consumption_kwh for r in readings]
    
    return jsonify({"labels": labels, "data": values})

@app.route('/api/bills')
@login_required
def api_bills():
    meter = Meter.query.filter_by(user_id=current_user.id).first()
    if not meter:
        return jsonify({"bills": []})
    bills = Bill.query.filter_by(meter_id=meter.id).order_by(Bill.billing_period_end.desc()).all()
    
    bill_data = []
    for b in bills:
        bill_data.append({
            "id": b.id,
            "period": f"{b.billing_period_start.strftime('%b %d, %Y')} - {b.billing_period_end.strftime('%b %d, %Y')}",
            "consumption": b.total_consumption_kwh,
            "amount": b.amount_due,
            "status": "Paid" if b.is_paid else "Pending",
            "details": json.loads(b.details)
        })
        
    return jsonify({"bills": bill_data})

@app.route('/api/pay_bill/<int:bill_id>', methods=['POST'])
@login_required
def pay_bill(bill_id):
    meter = Meter.query.filter_by(user_id=current_user.id).first()
    if not meter:
        return jsonify({"success": False, "message": "No meter found."}), 404

    bill = Bill.query.filter_by(id=bill_id, meter_id=meter.id).first()
    if not bill:
        return jsonify({"success": False, "message": "Bill not found."}), 404
    
    if bill.is_paid:
        return jsonify({"success": False, "message": "Bill is already paid."}), 400

    bill.is_paid = True
    db.session.commit()
    return jsonify({"success": True, "message": "Payment successful! Your bill has been marked as paid."})

if __name__ == '__main__':
    with app.app_context():
        # Always ensure tables exist
        db.create_all()
        # Only generate mock data if the users table is empty
        if not User.query.first():
            print("Generating mock data...")
            generate_mock_data(app)
            
    app.run(debug=True, port=5000)
