import sqlite3
from datetime import datetime
import re
from contextlib import contextmanager
import hashlib
import secrets

DATABASE = 'calorie_tracker.db'

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token():
    """Generate a random authentication token"""
    return secrets.token_urlsafe(32)

def init_db():
    """Initialize the database with required tables"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Table for users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table for user sessions/tokens
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Table for individual calorie entries (add user_id)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS calorie_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                food_items TEXT NOT NULL,
                total_calories INTEGER NOT NULL,
                analysis_text TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Table for daily totals (add user_id)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_totals (
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                total_calories INTEGER NOT NULL,
                entry_count INTEGER NOT NULL,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, date),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        print("Database initialized successfully with authentication tables")

# ============= User Authentication Functions =============

def create_user(username, email, password):
    """Create a new user account"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        password_hash = hash_password(password)
        
        try:
            cursor.execute('''
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
            ''', (username, email, password_hash))
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None  # User already exists

def authenticate_user(username, password):
    """Authenticate a user and return user info"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        password_hash = hash_password(password)
        
        cursor.execute('''
            SELECT id, username, email FROM users
            WHERE username = ? AND password_hash = ?
        ''', (username, password_hash))
        
        return cursor.fetchone()

def create_session(user_id):
    """Create a new session token for a user"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        token = generate_token()
        expires_at = datetime.now().timestamp() + (30 * 24 * 60 * 60)  # 30 days
        
        cursor.execute('''
            INSERT INTO user_sessions (token, user_id, expires_at)
            VALUES (?, ?, ?)
        ''', (token, user_id, datetime.fromtimestamp(expires_at)))
        
        return token

def validate_token(token):
    """Validate a session token and return user_id"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id FROM user_sessions
            WHERE token = ? AND expires_at > datetime('now')
        ''', (token,))
        
        result = cursor.fetchone()
        return result['user_id'] if result else None

def delete_session(token):
    """Delete a session (logout)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM user_sessions WHERE token = ?', (token,))

def extract_calories(analysis_text):
    """Extract total calories from the AI analysis text"""
    # Look for "Total calories -> X" or "Total calories: X" or similar patterns
    patterns = [
        r'Total calories[:\->\s]+(\d+)',
        r'total[:\s]+(\d+)\s*calories',
        r'(\d+)\s*total calories'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, analysis_text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    
    # If no total found, try to sum all individual calorie counts
    calories = re.findall(r'(\d+)\s*calories', analysis_text, re.IGNORECASE)
    if calories:
        return sum(int(cal) for cal in calories)
    
    return 0

def save_entry(analysis_text, total_calories, user_id):
    """Save a calorie entry to the database and update daily totals"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Extract food items (first line or first 200 chars)
        food_items_lines = [line.strip() for line in analysis_text.split('\n') if line.strip()]
        food_items = food_items_lines[0][:200] if food_items_lines else "Food item"
        
        # Insert individual entry
        cursor.execute('''
            INSERT INTO calorie_entries (user_id, date, food_items, total_calories, analysis_text)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, today, food_items, total_calories, analysis_text))
        
        entry_id = cursor.lastrowid
        
        # Update or insert daily total
        cursor.execute('''
            INSERT INTO daily_totals (user_id, date, total_calories, entry_count)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(user_id, date) DO UPDATE SET
                total_calories = total_calories + ?,
                entry_count = entry_count + 1,
                last_updated = CURRENT_TIMESTAMP
        ''', (user_id, today, total_calories, total_calories))
        
    return entry_id

def update_entry(entry_id, analysis_text, new_calories):
    """Update an existing entry with corrected information"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get the old entry details
        cursor.execute('''
            SELECT date, total_calories, user_id FROM calorie_entries WHERE id = ?
        ''', (entry_id,))
        
        entry = cursor.fetchone()
        if not entry:
            return None
        
        date, old_calories, user_id = entry
        calories_diff = new_calories - old_calories
        
        # Extract food items from new analysis
        food_items_lines = [line.strip() for line in analysis_text.split('\n') if line.strip()]
        food_items = food_items_lines[0][:200] if food_items_lines else "Food item"
        
        # Update the entry
        cursor.execute('''
            UPDATE calorie_entries
            SET food_items = ?,
                total_calories = ?,
                analysis_text = ?,
                timestamp = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (food_items, new_calories, analysis_text, entry_id))
        
        # Update daily total (adjust by the difference)
        cursor.execute('''
            UPDATE daily_totals
            SET total_calories = total_calories + ?,
                last_updated = CURRENT_TIMESTAMP
            WHERE user_id = ? AND date = ?
        ''', (calories_diff, user_id, date))
        
    return entry_id

def get_daily_total(date=None, user_id=None):
    """Get the total calories for a specific date (defaults to today)"""
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT date, total_calories, entry_count, last_updated
            FROM daily_totals
            WHERE date = ? AND user_id = ?
        ''', (date, user_id))
        
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

def get_all_daily_totals(limit=30, user_id=None):
    """Get daily totals for the last N days"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT date, total_calories, entry_count, last_updated
            FROM daily_totals
            WHERE user_id = ?
            ORDER BY date DESC
            LIMIT ?
        ''', (user_id, limit))
        
        return [dict(row) for row in cursor.fetchall()]

def get_entries_by_date(date=None, user_id=None):
    """Get all entries for a specific date (defaults to today)"""
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, date, food_items, total_calories, analysis_text, timestamp
            FROM calorie_entries
            WHERE date = ? AND user_id = ?
            ORDER BY timestamp DESC
        ''', (date, user_id))
        
        return [dict(row) for row in cursor.fetchall()]

def get_weekly_summary(user_id=None):
    """Get a summary of the last 7 days"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                date,
                total_calories,
                entry_count
            FROM daily_totals
            WHERE date >= date('now', '-7 days') AND user_id = ?
            ORDER BY date DESC
        ''', (user_id,))
        
        return [dict(row) for row in cursor.fetchall()]

def delete_entry(entry_id, user_id=None):
    """Delete a specific entry and update daily totals"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get entry details before deleting (with user_id check)
        if user_id:
            cursor.execute('''
                SELECT date, total_calories, user_id FROM calorie_entries 
                WHERE id = ? AND user_id = ?
            ''', (entry_id, user_id))
        else:
            cursor.execute('''
                SELECT date, total_calories, user_id FROM calorie_entries WHERE id = ?
            ''', (entry_id,))
        entry = cursor.fetchone()
        
        if not entry:
            return False
        
        date, calories, entry_user_id = entry
        
        # Delete the entry
        cursor.execute('DELETE FROM calorie_entries WHERE id = ?', (entry_id,))
        
        # Update daily total
        cursor.execute('''
            UPDATE daily_totals
            SET total_calories = total_calories - ?,
                entry_count = entry_count - 1,
                last_updated = CURRENT_TIMESTAMP
            WHERE date = ? AND user_id = ?
        ''', (calories, date, entry_user_id))
        
        # If no more entries for this day, delete the daily total
        cursor.execute('''
            DELETE FROM daily_totals
            WHERE date = ? AND entry_count <= 0 AND user_id = ?
        ''', (date, entry_user_id))
        
        return True

def clear_all_data(user_id=None):
    """Clear all data from the database for a specific user or all data"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if user_id:
            # Clear only this user's data
            cursor.execute('DELETE FROM calorie_entries WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM daily_totals WHERE user_id = ?', (user_id,))
        else:
            # Clear all data (admin function)
            cursor.execute('DELETE FROM calorie_entries')
            cursor.execute('DELETE FROM daily_totals')
            cursor.execute('DELETE FROM users')
            cursor.execute('DELETE FROM user_sessions')
        return True

if __name__ == '__main__':
    # Initialize database when run directly
    init_db()
    print("Database setup complete!")
