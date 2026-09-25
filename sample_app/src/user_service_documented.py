"""User service module for the sample application.

Provides database-backed user management operations including authentication,
CRUD operations, and score calculation.

Note:
    This module contains intentional security vulnerabilities for demo/review
    purposes. Do NOT use this code in production.
"""
import sqlite3
import hashlib
import os
import pickle
import subprocess

# Hardcoded secret — intentional vulnerability for demo
DB_PASSWORD = "s3cr3tP@ssw0rd123"
API_KEY = "sk-prod-abc123XYZ789hardcoded"


def get_db_connection():
    """Open and return a connection to the application SQLite database.

    Returns:
        sqlite3.Connection: An open connection to ``app.db``.
    """
    conn = sqlite3.connect("app.db")
    return conn


def get_user(username):
    """Retrieve a single user record from the database by username.

    Note:
        This function constructs the SQL query via string concatenation and is
        intentionally vulnerable to SQL injection for demo purposes.

    Args:
        username (str): The username to look up.

    Returns:
        tuple | None: A row tuple ``(id, username, password_hash, email)`` if
        the user exists, or ``None`` if no matching record is found.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    # SQL injection vulnerability — intentional for demo
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()
    return result


def authenticate_user(username, password):
    """Verify a username/password pair against the stored credential.

    Note:
        Passwords are hashed with MD5, which is cryptographically weak and
        intentionally insecure for demo purposes.

    Args:
        username (str): The username to authenticate.
        password (str): The plain-text password to verify.

    Returns:
        bool: ``True`` if the credentials are valid, ``False`` otherwise.
    """
    user = get_user(username)
    if user:
        # Weak hashing — intentional for demo
        hashed = hashlib.md5(password.encode()).hexdigest()
        if user[2] == hashed:
            return True
    return False


def run_report(report_name):
    """Execute a named report script as a subprocess.

    Note:
        The report name is passed directly to the shell without sanitisation,
        making this function intentionally vulnerable to command injection for
        demo purposes.

    Args:
        report_name (str): The filename of the report script located under the
            ``reports/`` directory (e.g. ``"monthly_summary.py"``).

    Returns:
        None
    """
    # Command injection vulnerability — intentional for demo
    subprocess.call("python reports/" + report_name, shell=True)


def load_user_preferences(data_bytes):
    """Deserialize user preferences from a raw byte string.

    Note:
        Uses ``pickle.loads``, which executes arbitrary Python objects embedded
        in the byte string. This is intentionally unsafe deserialization for
        demo purposes.

    Args:
        data_bytes (bytes): A pickle-serialized byte string representing user
            preference data.

    Returns:
        Any: The deserialized Python object (typically a ``dict``).
    """
    # Unsafe deserialization — intentional for demo
    return pickle.loads(data_bytes)


def create_user(username, password, email):
    """Insert a new user record into the database.

    The password is hashed with MD5 before storage.

    Note:
        The INSERT statement is built with ``%`` string formatting and is
        intentionally vulnerable to SQL injection for demo purposes.

    Args:
        username (str): The desired username for the new account.
        password (str): The plain-text password; stored as an MD5 hex digest.
        email (str): The user's email address.

    Returns:
        None
    """
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
    """Update the email address for an existing user.

    Note:
        The UPDATE statement is constructed via string concatenation and is
        intentionally vulnerable to SQL injection for demo purposes.

    Args:
        user_id (int): The numeric primary key of the user to update.
        new_email (str): The replacement email address.

    Returns:
        None
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    # Another SQL injection — intentional for demo
    cursor.execute(
        "UPDATE users SET email = '" + new_email + "' WHERE id = " + str(user_id)
    )
    conn.commit()
    conn.close()


def delete_user(user_id):
    """Remove a user record from the database by its primary key.

    Args:
        user_id (int): The numeric primary key of the user to delete.

    Returns:
        None
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def get_all_users():
    """Fetch every user record from the database.

    Returns:
        list[tuple]: A list of row tuples
        ``[(id, username, password_hash, email), ...]``. Returns an empty list
        if the users table is empty.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    results = cursor.fetchall()
    conn.close()
    return results


def calculate_user_score(activity_count, bonus, multiplier):
    """Calculate a gamification score for a standard user.

    The score is computed using a tiered multiplier scheme based on
    ``activity_count``, with an optional flat bonus applied at each tier:

    * ``activity_count < 10``   → ``activity_count × multiplier``
    * ``10 ≤ activity_count < 50`` → ``activity_count × multiplier × 1.5``
      (+ ``bonus × 2`` if bonus is non-zero)
    * ``50 ≤ activity_count < 100`` → ``activity_count × multiplier × 2``
      (+ ``bonus × 3`` if bonus is non-zero)
    * ``activity_count ≥ 100`` → ``activity_count × multiplier × 3``
      (+ ``bonus × 5`` if bonus is non-zero)

    Args:
        activity_count (int): The number of activities completed by the user.
            A value of 0 or less returns a score of 0.
        bonus (float): An optional bonus amount added on top of the base score
            at each tier. Pass ``0`` to omit the bonus.
        multiplier (float): A scaling factor applied to the activity count
            at every tier.

    Returns:
        float: The computed score. Returns ``0`` when ``activity_count <= 0``.
    """
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
    """Calculate a gamification score for an administrator user.

    Uses the same tiered multiplier scheme as :func:`calculate_user_score`.
    The scoring tiers are:

    * ``activity_count < 10``   → ``activity_count × multiplier``
    * ``10 ≤ activity_count < 50`` → ``activity_count × multiplier × 1.5``
      (+ ``bonus × 2`` if bonus is non-zero)
    * ``50 ≤ activity_count < 100`` → ``activity_count × multiplier × 2``
      (+ ``bonus × 3`` if bonus is non-zero)
    * ``activity_count ≥ 100`` → ``activity_count × multiplier × 3``
      (+ ``bonus × 5`` if bonus is non-zero)

    Note:
        This function duplicates the logic of :func:`calculate_user_score` and
        is retained as an intentional code-smell for demo purposes.

    Args:
        activity_count (int): The number of activities completed by the admin.
            A value of 0 or less returns a score of 0.
        bonus (float): An optional bonus amount added on top of the base score
            at each tier. Pass ``0`` to omit the bonus.
        multiplier (float): A scaling factor applied to the activity count
            at every tier.

    Returns:
        float: The computed score. Returns ``0`` when ``activity_count <= 0``.
    """
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
