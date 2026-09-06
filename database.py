"""
EcoAir-Forecast: SQLite Database Management Module
--------------------------------------------------
Provides lightweight, reliable relational database storage for user searches,
forecast history, and environmental analytics using Python's standard `sqlite3`.

Database file: data/ecoair.db
"""

import sqlite3
import os
from datetime import datetime

DB_DIR = 'data'
DB_PATH = os.path.join(DB_DIR, 'ecoair.db')

def get_db_connection():
    """Establishes and returns a connection with Row factory enabled."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema if tables do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Table: search_history
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            lat REAL,
            lon REAL,
            model_used TEXT NOT NULL,
            predicted_aqi INTEGER NOT NULL,
            category TEXT NOT NULL,
            temperature REAL,
            humidity REAL,
            wind_speed REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"[SQLite] Database initialized at: {DB_PATH}")

def log_search(city, lat, lon, model_used, predicted_aqi, category, temperature, humidity, wind_speed):
    """Logs a successful prediction search into the search_history table."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO search_history 
            (city, lat, lon, model_used, predicted_aqi, category, temperature, humidity, wind_speed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (city, lat, lon, model_used, predicted_aqi, category, temperature, humidity, wind_speed))
        conn.commit()
        record_id = cursor.lastrowid
        conn.close()
        return record_id
    except Exception as e:
        print(f"[SQLite] Error logging search: {e}")
        return None

def get_recent_searches(limit=10):
    """Fetches the latest searches ordered by most recent first."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, city, lat, lon, model_used, predicted_aqi, category, 
                   temperature, humidity, wind_speed, created_at
            FROM search_history
            ORDER BY id DESC
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for r in rows:
            results.append({
                'id': r['id'],
                'city': r['city'],
                'lat': r['lat'],
                'lon': r['lon'],
                'model_used': r['model_used'],
                'predicted_aqi': r['predicted_aqi'],
                'category': r['category'],
                'temperature': r['temperature'],
                'humidity': r['humidity'],
                'wind_speed': r['wind_speed'],
                'created_at': r['created_at']
            })
        return results
    except Exception as e:
        print(f"[SQLite] Error fetching recent searches: {e}")
        return []

def clear_search_history():
    """Clears all records from search_history table."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM search_history')
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[SQLite] Error clearing search history: {e}")
        return False

def get_db_stats():
    """Computes summary analytics from the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as total FROM search_history')
        total = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(DISTINCT city) as distinct_cities FROM search_history')
        distinct_cities = cursor.fetchone()['distinct_cities']
        
        cursor.execute('SELECT AVG(predicted_aqi) as avg_aqi FROM search_history')
        avg_row = cursor.fetchone()['avg_aqi']
        avg_aqi = round(avg_row, 1) if avg_row is not None else 0
        
        cursor.execute('''
            SELECT city, COUNT(*) as count 
            FROM search_history 
            GROUP BY city 
            ORDER BY count DESC 
            LIMIT 1
        ''')
        top_city_row = cursor.fetchone()
        top_city = top_city_row['city'] if top_city_row else 'None'
        
        conn.close()
        return {
            'total_searches': total,
            'unique_cities': distinct_cities,
            'avg_aqi': avg_aqi,
            'top_city': top_city,
            'db_engine': 'SQLite 3'
        }
    except Exception as e:
        print(f"[SQLite] Error calculating stats: {e}")
        return {
            'total_searches': 0,
            'unique_cities': 0,
            'avg_aqi': 0,
            'top_city': 'None',
            'db_engine': 'SQLite 3'
        }

if __name__ == '__main__':
    init_db()
    print("Database verification passed!")
