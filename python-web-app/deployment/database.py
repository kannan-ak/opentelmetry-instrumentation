import sqlite3
from datetime import datetime
import time


def init_db():
    conn = sqlite3.connect('search_history.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            city TEXT NOT NULL,
            temperature REAL NOT NULL,
            description TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_search(city, temperature, description):   
    time.sleep(2)
    conn = sqlite3.connect('search_history.db')
    cursor = conn.cursor()     
    cursor.execute('''
        INSERT INTO search_history (timestamp, city, temperature, description)
        VALUES (?, ?, ?, ?)
    ''', (datetime.now().isoformat(timespec="seconds", sep=" "), city, temperature, description))   
    conn.commit()
    conn.close()

def get_recent_searches(limit=5):
    conn = sqlite3.connect('search_history.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT timestamp, city, temperature, description
        FROM search_history
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows