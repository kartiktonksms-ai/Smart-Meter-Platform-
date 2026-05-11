import random
from datetime import datetime, timedelta
import json
from werkzeug.security import generate_password_hash
from models import db, User, Meter, Reading, Bill

def calculate_tier_pricing(consumption):
    """
    Tier 1: 0-100 kWh -> ₹10.00/kWh
    Tier 2: 101-300 kWh -> ₹15.00/kWh
    Tier 3: 301+ kWh -> ₹25.00/kWh
    """
    amount = 0
    breakdown = []
    remaining = consumption
    
    if remaining > 0:
        t1 = min(remaining, 100)
        cost1 = t1 * 10.00
        amount += cost1
        breakdown.append({"tier": "1 (0-100 kWh)", "kwh": t1, "rate": 10.00, "cost": cost1})
        remaining -= t1
    
    if remaining > 0:
        t2 = min(remaining, 200)
        cost2 = t2 * 15.00
        amount += cost2
        breakdown.append({"tier": "2 (101-300 kWh)", "kwh": t2, "rate": 15.00, "cost": cost2})
        remaining -= t2
        
    if remaining > 0:
        t3 = remaining
        cost3 = t3 * 25.00
        amount += cost3
        breakdown.append({"tier": "3 (301+ kWh)", "kwh": t3, "rate": 25.00, "cost": cost3})
        
    return amount, breakdown

def generate_mock_data_for_meter(meter_id, user_id):
    """Generates mock data for a specific meter to be used during sign-up."""
    from models import db, Reading, Bill
    # Generate 30 days of hourly readings
    end_time = datetime.now()
    start_time = end_time - timedelta(days=30)
    
    current_time = start_time
    readings = []
    total_kwh = 0
    
    while current_time <= end_time:
        # Simulate daily peaks (e.g., mornings 7-9 AM, evenings 6-9 PM)
        hour = current_time.hour
        if 7 <= hour <= 9 or 18 <= hour <= 21:
            consumption = random.uniform(1.5, 3.5)
        elif 1 <= hour <= 5: # Night time low usage
            consumption = random.uniform(0.1, 0.4)
        else:
            consumption = random.uniform(0.5, 1.5)
        
        readings.append(Reading(
            meter_id=meter_id,
            timestamp=current_time,
            consumption_kwh=round(consumption, 2)
        ))
        
        total_kwh += consumption
        current_time += timedelta(hours=1)
        
    db.session.bulk_save_objects(readings)
    
    # Calculate bill for the past 30 days
    amount_due, breakdown = calculate_tier_pricing(total_kwh)
    
    bill = Bill(
        meter_id=meter_id,
        billing_period_start=start_time,
        billing_period_end=end_time,
        total_consumption_kwh=round(total_kwh, 2),
        amount_due=round(amount_due, 2),
        details=json.dumps(breakdown)
    )
    db.session.add(bill)
    db.session.commit()

def generate_mock_data(app):
    # Clear existing data and recreate
    db.drop_all()
    db.create_all()
    
    # Create a mock user
    user = User(
        name="John Doe", 
        email="john.doe@example.com", 
        address="123 Smart Ave, Tech City",
        password_hash=generate_password_hash("password123", method="pbkdf2:sha256")
    )
    db.session.add(user)
    db.session.flush() # flush to get user id
    
    # Create a smart meter
    meter = Meter(meter_number="SM-123456789", type="Residential", user_id=user.id)
    db.session.add(meter)
    db.session.flush()
    
    generate_mock_data_for_meter(meter.id, user.id)
    
    print("Mock data generated successfully.")
