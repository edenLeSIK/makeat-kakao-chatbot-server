import os
import sqlite3
from datetime import datetime

DATABASE = 'data/users.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def close_db_connection(conn):
    conn.commit()
    conn.close()

def initialize_database():
    if not os.path.exists(DATABASE):
        conn = sqlite3.connect(DATABASE)
        conn.close()
    create_tables()

def create_tables():
    create_users_table()
    create_weight_history_table()
    create_goal_weight_history_table()

def create_users_table():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, name TEXT, birthdate TEXT, gender TEXT, height INTEGER, weight INTEGER, goal_weight INTEGER, bmr REAL, created_date TEXT)')

def create_weight_history_table():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS weight_history (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, weight INTEGER, date TEXT)')

def create_goal_weight_history_table():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS goal_weight_history (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, goal_weight INTEGER, date TEXT)')

def insert_or_update_user(user_id, birthdate, gender, height, weight, goal_weight, bmr, created_date):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()

        if not user:
            cursor.execute('INSERT INTO users (user_id, name, birthdate, gender, height, weight, goal_weight, bmr, created_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', (user_id, "", birthdate, gender, height, weight, goal_weight, bmr, created_date))
        else:
            cursor.execute('UPDATE users SET birthdate = ?, gender = ?, height = ?, weight = ?, goal_weight = ?, bmr = ?, created_date = ? WHERE user_id = ?', (birthdate, gender, height, weight, goal_weight, bmr, created_date, user_id))

def get_user(user_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        return user

def insert_weight_history(user_id, weight, date):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO weight_history (user_id, weight, date) VALUES (?, ?, ?)', (user_id, weight, date))

def insert_goal_weight_history(user_id, goal_weight, date):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO goal_weight_history (user_id, goal_weight, date) VALUES (?, ?, ?)', (user_id, goal_weight, date))

def get_weight_history(user_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM weight_history WHERE user_id = ? ORDER BY date DESC', (user_id,))
        weight_history = cursor.fetchall()
    return weight_history[::-1]

def get_goal_weight_history(user_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM goal_weight_history WHERE user_id = ? ORDER BY date DESC', (user_id,))
        goal_weight_history = cursor.fetchall()
    return goal_weight_history[::-1]

def get_date_in_yymmdd_format(date):
    return datetime.strptime(date, "%Y-%m-%d").strftime("%y%m%d")