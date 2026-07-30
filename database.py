import sqlite3
from datetime import datetime

DB_PATH = "driver_monitor.db"

def create_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS drivers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        license_no TEXT,
        phone TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS violations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        driver_id INTEGER,
        violation_type TEXT,
        screenshot_path TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        trip_id INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS trips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        driver_id INTEGER,
        start_time TIMESTAMP,
        end_time TIMESTAMP,
        total_violations INTEGER DEFAULT 0,
        verdict TEXT,
        FOREIGN KEY(driver_id) REFERENCES drivers(id)
    )''')
    conn.commit()
    conn.close()

def add_driver(name, license_no, phone=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO drivers (name, license_no, phone) VALUES (?, ?, ?)",
              (name, license_no, phone))
    driver_id = c.lastrowid
    conn.commit()
    conn.close()
    return driver_id

def start_trip(driver_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO trips (driver_id, start_time) VALUES (?, ?)",
              (driver_id, datetime.now()))
    trip_id = c.lastrowid
    conn.commit()
    conn.close()
    return trip_id

def end_trip(trip_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM violations WHERE trip_id=?", (trip_id,))
    total = c.fetchone()[0]
    if total == 0:
        verdict = "EXCELLENT"
    elif total <= 3:
        verdict = "SAFE"
    elif total <= 7:
        verdict = "WARNING"
    else:
        verdict = "UNSAFE"
    c.execute("""UPDATE trips SET end_time=?, total_violations=?, verdict=?
                 WHERE id=?""", (datetime.now(), total, verdict, trip_id))
    c.execute("""SELECT d.name, d.license_no, t.start_time, t.end_time,
                        t.total_violations, t.verdict
                 FROM trips t JOIN drivers d ON t.driver_id=d.id
                 WHERE t.id=?""", (trip_id,))
    row = c.fetchone()
    c.execute("""SELECT violation_type, COUNT(*) as cnt
                 FROM violations WHERE trip_id=?
                 GROUP BY violation_type""", (trip_id,))
    breakdown = dict(c.fetchall())
    conn.commit()
    conn.close()
    return {
        "driver_name": row[0],
        "license_no":  row[1],
        "start_time":  row[2],
        "end_time":    row[3],
        "total":       row[4],
        "verdict":     row[5],
        "breakdown":   breakdown
    }
def get_all_trips(driver_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT id, start_time, end_time, total_violations, verdict
                 FROM trips WHERE driver_id=? AND end_time IS NOT NULL
                 ORDER BY start_time DESC""", (driver_id,))
    rows = c.fetchall()
    conn.close()
    return [{
        "trip_id": r[0],
        "start_time": r[1],
        "end_time": r[2],
        "total": r[3],
        "verdict": r[4]
    } for r in rows]


def find_driver_by_license(license_no):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name FROM drivers WHERE license_no=? ORDER BY id DESC LIMIT 1", (license_no,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "name": row[1]}
    return None

def log_violation(driver_id, violation_type, screenshot_path="", trip_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""INSERT INTO violations
                 (driver_id, violation_type, screenshot_path, trip_id)
                 VALUES (?, ?, ?, ?)""",
              (driver_id, violation_type, screenshot_path, trip_id))
    conn.commit()
    conn.close()

def get_violations(driver_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT violation_type, timestamp
                 FROM violations WHERE driver_id=?
                 ORDER BY timestamp DESC""", (driver_id,))
    rows = c.fetchall()
    conn.close()
    return [{"type": r[0], "time": r[1]} for r in rows]

def get_violation_counts(driver_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT violation_type, COUNT(*)
                 FROM violations WHERE driver_id=?
                 GROUP BY violation_type""", (driver_id,))
    rows = c.fetchall()
    conn.close()
    return dict(rows)

def get_all_drivers():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, license_no FROM drivers")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "license": r[2]} for r in rows]