# ⚡ Smart Meter Platform

A full-stack web application that simulates a residential smart electricity meter management system. Users can register, monitor their real-time energy consumption, analyze usage trends, and manage their electricity bills — all from a clean, interactive dashboard.

---

## 📸 Features

- **User Authentication** — Secure signup/login with hashed passwords (PBKDF2-SHA256)
- **Smart Meter Assignment** — Each user is automatically assigned a unique smart meter on registration
- **Live Dashboard** — View 30-day energy consumption, current estimated bill, and recent billing history
- **Bill Alerts** — Automatic alerts for bills due within 5 days or overdue
- **Analytics Page** — Hourly and daily consumption charts
- **Billing Page** — Full bill history with tier pricing breakdown and in-app payment
- **Mock Data Simulator** — Realistic hourly consumption patterns (morning/evening peaks, night lows) seeded on first run

---

## 🗂️ Project Structure

```
smart meter platform/
├── app.py              # Flask application, routes & REST API endpoints
├── models.py           # SQLAlchemy database models (User, Meter, Reading, Bill)
├── simulator.py        # Mock data generator & tier pricing engine
├── requirements.txt    # Python dependencies
├── platform.db         # SQLite database (auto-created on first run)
├── templates/
│   ├── base.html       # Shared layout & navigation
│   ├── login.html      # Login page
│   ├── signup.html     # Registration page
│   ├── dashboard.html  # Main dashboard
│   ├── analytics.html  # Consumption analytics & charts
│   └── billing.html    # Bill management & payment
└── static/
    └── css/            # Application stylesheets
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- `pip`

### Installation

1. **Clone the repository**

   ```bash
   git clone <your-repo-url>
   cd "smart meter platform"
   ```

2. **Create and activate a virtual environment**

   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**

   ```bash
   python app.py
   ```

5. Open your browser and navigate to `http://127.0.0.1:5000`

> **First Run:** If no users exist in the database, the app automatically seeds a demo account and 30 days of mock consumption data.

---

## 🔑 Demo Account (Auto-seeded)

| Field    | Value                    |
|----------|--------------------------|
| Email    | `john.doe@example.com`   |
| Password | `password123`            |

You can also create your own account via the **Sign Up** page — a smart meter and 30 days of historical data will be generated automatically.

---

## 💡 Tier Pricing Model

Bills are calculated using a progressive tier system (Indian Rupees):

| Tier   | Consumption Range | Rate (₹/kWh) |
|--------|-------------------|--------------|
| Tier 1 | 0 – 100 kWh       | ₹10.00       |
| Tier 2 | 101 – 300 kWh     | ₹15.00       |
| Tier 3 | 301+ kWh          | ₹25.00       |

---

## 🛠️ Tech Stack

| Layer     | Technology                          |
|-----------|-------------------------------------|
| Backend   | Python 3, Flask 3.0                 |
| ORM       | Flask-SQLAlchemy 3.1                |
| Auth      | Flask-Login 0.6, Werkzeug           |
| Database  | SQLite (via SQLAlchemy)             |
| Frontend  | HTML5, Vanilla CSS, JavaScript      |

---

## 📡 REST API Endpoints

| Method | Endpoint                     | Description                          |
|--------|------------------------------|--------------------------------------|
| GET    | `/api/summary`               | Dashboard summary (consumption, bill, alerts) |
| GET    | `/api/daily_readings`        | Daily kWh totals for chart           |
| GET    | `/api/hourly_readings`       | Last 24-hour hourly readings         |
| GET    | `/api/bills`                 | Full billing history with tier details |
| POST   | `/api/pay_bill/<bill_id>`    | Mark a specific bill as paid         |

All endpoints require an authenticated session.

---

## ⚠️ Notes

- The `SECRET_KEY` in `app.py` is a placeholder. **Change it before deploying to production.**
- `platform.db` is a local SQLite file. For production, migrate to PostgreSQL or another managed database.
- The simulator generates data patterns that mirror real-world residential usage (peaks in the morning 7–9 AM and evening 6–9 PM, low usage at night 1–5 AM).

---

## 📄 License

This project is for educational/demo purposes.
