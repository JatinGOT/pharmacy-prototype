"""Tiny SQLite storage. One table: one row per medicine line on a verified prescription.
We store ONLY medicine, strength, date, availability status. No patient details."""
import os, sqlite3, random, datetime
import pandas as pd
from sample_data import SAMPLE_MEDICINES

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "data", "pharmacy.db")
FORMULARY = os.path.join(BASE, "data", "formulary.csv")


def _c():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    return sqlite3.connect(DB)


def init():
    with _c() as c:
        c.execute("CREATE TABLE IF NOT EXISTS records(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                  "medicine TEXT, strength TEXT, record_date TEXT, status TEXT, source TEXT)")
        if c.execute("SELECT COUNT(*) FROM records WHERE source='sample'").fetchone()[0] == 0:
            rng = random.Random(42)
            picks = rng.choices(SAMPLE_MEDICINES, weights=[m[2] for m in SAMPLE_MEDICINES], k=400)
            for name, strength, _, p_unavail in picks:
                day = datetime.date.today() - datetime.timedelta(days=rng.randint(0, 89))
                if rng.random() < p_unavail:
                    status = "Unavailable"
                else:
                    status = "Sold" if rng.random() < 0.9 else "Not recorded"
                c.execute("INSERT INTO records(medicine,strength,record_date,status,source) VALUES(?,?,?,?,'sample')",
                          (name, strength, day.isoformat(), status))


def add_records(items):
    """items = list of (medicine, strength, status)"""
    today = datetime.date.today().isoformat()
    with _c() as c:
        for med, strength, status in items:
            c.execute("INSERT INTO records(medicine,strength,record_date,status,source) VALUES(?,?,?,?,'verified')",
                      (med.strip(), strength.strip(), today, status))


def load_records(include_sample=True):
    q = "SELECT * FROM records" + ("" if include_sample else " WHERE source='verified'")
    with _c() as c:
        return pd.read_sql_query(q, c)


def clear_my_records():
    with _c() as c:
        c.execute("DELETE FROM records WHERE source='verified'")


def load_formulary():
    try:
        return set(pd.read_csv(FORMULARY)["medicine"].astype(str).str.strip().str.lower())
    except Exception:
        return set()
