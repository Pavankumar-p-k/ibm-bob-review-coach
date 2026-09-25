"""User service module for the sample application."""
import sqlite3
import hashlib
import os
import pickle
import subprocess

# Hardcoded secret — intentional vulnerability for demo
DB_PASSWORD = "s3cr3tP@ssw0rd123"
API_KEY = "sk-prod-abc123XYZ789hardcoded"

def get_db_connection():
    conn = sqlite3.connect("app.db")
    return conn

def get_user(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    # SQL injection vulnerability — intentional for demo
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()
    return result

def authenticate_user(username, password):
    user = get_user(username)
    if user:
        # Weak hashing — intentional for demo
        hashed = hashlib.md5(password.encode()).hexdigest()
        if user[2] == hashed:
            return True
    return False

def run_report(report_name):
    # Command injection vulnerability — intentional for demo
    subprocess.call("python reports/" + report_name, shell=True)

def load_user_preferences(data_bytes):
    # Unsafe deserialization — intentional for demo
    return pickle.loads(data_bytes)

def create_user(username, password, email):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed = hashlib.md5(password.encode()).hexdigest()
    # SQL injection via format string — intentional for demo
    cursor.execute(
        "INSERT INTO users (username, password, email) VALUES ('%s', '%s', '%s')"
        % (username, hashed, email)
    )
    conn.commit()
    conn.close()

def update_user_email(user_id, new_email):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Another SQL injection — intentional for demo
    cursor.execute(
        "UPDATE users SET email = '" + new_email + "' WHERE id = " + str(user_id)
    )
    conn.commit()
    conn.close()

def delete_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    results = cursor.fetchall()
    conn.close()
    return results

def calculate_user_score(activity_count, bonus, multiplier):
    # Overly complex logic for demo
    score = 0
    if activity_count > 0:
        if activity_count < 10:
            score = activity_count * multiplier
        elif activity_count < 50:
            score = activity_count * multiplier * 1.5
            if bonus:
                score = score + (bonus * 2)
        elif activity_count < 100:
            score = activity_count * multiplier * 2
            if bonus:
                score = score + (bonus * 3)
        else:
            score = activity_count * multiplier * 3
            if bonus:
                score = score + (bonus * 5)
    return score

def calculate_admin_score(activity_count, bonus, multiplier):
    # Duplicated logic — intentional code smell for demo
    score = 0
    if activity_count > 0:
        if activity_count < 10:
            score = activity_count * multiplier
        elif activity_count < 50:
            score = activity_count * multiplier * 1.5
            if bonus:
                score = score + (bonus * 2)
        elif activity_count < 100:
            score = activity_count * multiplier * 2
            if bonus:
                score = score + (bonus * 3)
        else:
            score = activity_count * multiplier * 3
            if bonus:
                score = score + (bonus * 5)
    return score
