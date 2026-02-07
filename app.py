from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime
import requests
from flask import Flask, render_template, request, redirect, flash
app = Flask(__name__)
app.secret_key = "supersecretkey"


app = Flask(__name__)
def get_live_rates():
    try:
        url = "https://api.metals.live/v1/spot"
        response = requests.get(url, timeout=5)
        data = response.json()

        gold_rate = None
        silver_rate = None

        for item in data:
            if item[0] == "gold":
                gold_rate = item[1]
            if item[0] == "silver":
                silver_rate = item[1]

        return gold_rate, silver_rate

    except:
        return None, None


# ---------------- DATABASE SETUP ---------------- #

conn = sqlite3.connect("database.db")
c = conn.cursor()

# Staff Table
c.execute("""
CREATE TABLE IF NOT EXISTS staff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    role TEXT,
    phone TEXT
)
""")

# Inventory Table
c.execute("""
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    weight REAL,
    type TEXT
)
""")

# Attendance Table
c.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    staff_id INTEGER,
    status TEXT,
    date TEXT
)
""")

# Rates Table
c.execute("""
CREATE TABLE IF NOT EXISTS rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gold REAL,
    silver REAL,
    date TEXT
)
""")

conn.commit()
conn.close()

# ---------------- HOME PAGE ---------------- #

import requests

@app.route("/")
def home():
    try:
        url = "https://api.metals.live/v1/spot"
        response = requests.get(url, timeout=5)
        data = response.json()

        gold_usd = data["gold"]      # per ounce
        silver_usd = data["silver"]  # per ounce

        USD_TO_INR = 83  # approx rate
        OUNCE_TO_GRAM = 31.1035

        gold_rate = round((gold_usd * USD_TO_INR) / OUNCE_TO_GRAM, 2)
        silver_rate = round((silver_usd * USD_TO_INR) / OUNCE_TO_GRAM, 2)

    except:
        gold_rate = "Unavailable"
        silver_rate = "Unavailable"

    return render_template(
        "index.html",
        gold_rate=gold_rate,
        silver_rate=silver_rate
    )


# ---------------- STAFF PAGE ---------------- #

@app.route("/staff", methods=["GET", "POST"])
def staff():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if request.method == "POST":
        name = request.form.get("name")
        role = request.form.get("role")
        phone = request.form.get("phone")

        if name and role and phone:
            c.execute(
                "INSERT INTO staff (name, role, phone) VALUES (?, ?, ?)",
                (name, role, phone)
            )
            conn.commit()
            flash("✅ Staff added successfully!", "success")
            return redirect("/staff")
        else:
            flash("❌ Please fill all fields", "error")

    c.execute("SELECT * FROM staff")
    staff_list = c.fetchall()
    conn.close()

    return render_template("staff.html", staff=staff_list)

@app.route("/delete_staff/<int:id>")
def delete_staff(id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("DELETE FROM staff WHERE id=?", (id,))
    conn.commit()
    conn.close()

    flash("🗑️ Staff deleted successfully", "success")
    return redirect("/staff")



# ---------------- INVENTORY PAGE ---------------- #

@app.route("/inventory", methods=["GET", "POST"])
def inventory():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if request.method == "POST":
        name = request.form.get("name")
        weight = request.form.get("weight")
        type_ = request.form.get("type")

        if name and weight and type_:
            c.execute(
                "INSERT INTO inventory (name, weight, type) VALUES (?, ?, ?)",
                (name, weight, type_)
            )
            conn.commit()

    c.execute("SELECT * FROM inventory")
    items = c.fetchall()

    conn.close()
    return render_template("inventory.html", items=items)
flash("✅ Item added successfully", "success")


@app.route("/delete_item/<int:id>")
def delete_item(id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("DELETE FROM inventory WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/inventory")
flash("🗑️ Item deleted", "success")

# ---------------- ATTENDANCE PAGE ---------------- #

@app.route("/attendance", methods=["GET", "POST"])
def attendance():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if request.method == "POST":
        staff_id = request.form.get("staff_id")
        status = request.form.get("status")
        date = datetime.now().strftime("%Y-%m-%d")

        if staff_id and status:
            c.execute(
                "INSERT INTO attendance (staff_id, status, date) VALUES (?, ?, ?)",
                (staff_id, status, date)
            )
            conn.commit()

    c.execute("SELECT * FROM staff")
    staff_list = c.fetchall()

    c.execute("""
        SELECT attendance.date, staff.name, attendance.status
        FROM attendance
        JOIN staff ON attendance.staff_id = staff.id
        ORDER BY attendance.date DESC
    """)
    records = c.fetchall()

    conn.close()

    return render_template("attendance.html", staff=staff_list, records=records)

# ---------------- RATES PAGE ---------------- #

@app.route("/rates", methods=["GET", "POST"])
def rates():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if request.method == "POST":
        gold = request.form.get("gold")
        silver = request.form.get("silver")
        date = datetime.now().strftime("%Y-%m-%d")

        if gold and silver:
            c.execute(
                "INSERT INTO rates (gold, silver, date) VALUES (?, ?, ?)",
                (gold, silver, date)
            )
            conn.commit()

    c.execute("SELECT * FROM rates ORDER BY date DESC LIMIT 1")
    latest = c.fetchone()

    conn.close()

    return render_template("rates.html", latest=latest)

# ---------------- REPORTS PAGE ---------------- #

@app.route("/reports")
def reports():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM staff")
    staff_count = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM inventory")
    inventory_count = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM attendance")
    attendance_count = c.fetchone()[0]

    conn.close()

    return render_template(
        "reports.html",
        staff_count=staff_count,
        inventory_count=inventory_count,
        attendance_count=attendance_count
    )

# ---------------- RUN APP ---------------- #

if __name__ == "__main__":
    app.run(debug=True)
