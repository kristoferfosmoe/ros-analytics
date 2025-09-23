import sqlite3
import os
from datetime import datetime

DB_PATH = "flight_data.db"

def init_database():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flight_name TEXT UNIQUE NOT NULL,
            mean_error REAL NOT NULL,
            std_error REAL NOT NULL,
            total_points INTEGER NOT NULL,
            date TEXT NOT NULL,
            beacon_lat REAL NOT NULL,
            beacon_lon REAL NOT NULL,
            beacon_alt REAL NOT NULL,
            plot_path TEXT NOT NULL,
            bag_path TEXT,
            csv_path TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def save_flight_data(flight_name, mean_error, std_error, total_points, 
                    beacon_lat, beacon_lon, beacon_alt, plot_path, bag_path=None, csv_path=None):
    """Save flight analysis results to database"""
    init_database()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO flights 
            (flight_name, mean_error, std_error, total_points, date, 
             beacon_lat, beacon_lon, beacon_alt, plot_path, bag_path, csv_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (flight_name, mean_error, std_error, total_points, date,
              beacon_lat, beacon_lon, beacon_alt, plot_path, bag_path, csv_path))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving flight data: {e}")
        return False
    finally:
        conn.close()

def get_all_flights():
    """Get all flights from database"""
    init_database()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM flights ORDER BY date DESC')
    flights = cursor.fetchall()
    
    conn.close()
    return flights

def get_flight_data(flight_name):
    """Get specific flight data"""
    init_database()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM flights WHERE flight_name = ?', (flight_name,))
    flight = cursor.fetchone()
    
    conn.close()
    
    if flight:
        return {
            'id': flight[0],
            'flight_name': flight[1],
            'mean_error': flight[2],
            'std_error': flight[3],
            'total_points': flight[4],
            'date': flight[5],
            'beacon_lat': flight[6],
            'beacon_lon': flight[7],
            'beacon_alt': flight[8],
            'plot_path': flight[9],
            'bag_path': flight[10],
            'csv_path': flight[11]
        }
    return None