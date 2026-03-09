import sqlite3
from datetime import datetime
import re
from contextlib import contextmanager

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

def init_db():
    """Initialize the database with required tables"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Table for individual calorie entries
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS calorie_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                food_items TEXT NOT NULL,
                total_calories INTEGER NOT NULL,
                analysis_text TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table for daily totals
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_totals (
                date TEXT PRIMARY KEY,
                total_calories INTEGER NOT NULL,
                entry_count INTEGER NOT NULL,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        print("Database initialized successfully")

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

def save_entry(analysis_text, total_calories):
    """Save a calorie entry to the database and update daily totals"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Extract food items (first line or first 200 chars)
        food_items_lines = [line.strip() for line in analysis_text.split('\n') if line.strip()]
        food_items = food_items_lines[0][:200] if food_items_lines else "Food item"
        
        # Insert individual entry
        cursor.execute('''
            INSERT INTO calorie_entries (date, food_items, total_calories, analysis_text)
            VALUES (?, ?, ?, ?)
        ''', (today, food_items, total_calories, analysis_text))
        
        entry_id = cursor.lastrowid
        
        # Update or insert daily total
        cursor.execute('''
            INSERT INTO daily_totals (date, total_calories, entry_count)
            VALUES (?, ?, 1)
            ON CONFLICT(date) DO UPDATE SET
                total_calories = total_calories + ?,
                entry_count = entry_count + 1,
                last_updated = CURRENT_TIMESTAMP
        ''', (today, total_calories, total_calories))
        
    return entry_id

def update_entry(entry_id, analysis_text, new_calories):
    """Update an existing entry with corrected information"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get the old entry details
        cursor.execute('''
            SELECT date, total_calories FROM calorie_entries WHERE id = ?
        ''', (entry_id,))
        
        entry = cursor.fetchone()
        if not entry:
            return None
        
        date, old_calories = entry
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
            WHERE date = ?
        ''', (calories_diff, date))
        
    return entry_id

def get_daily_total(date=None):
    """Get the total calories for a specific date (defaults to today)"""
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT date, total_calories, entry_count, last_updated
            FROM daily_totals
            WHERE date = ?
        ''', (date,))
        
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

def get_all_daily_totals(limit=30):
    """Get daily totals for the last N days"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT date, total_calories, entry_count, last_updated
            FROM daily_totals
            ORDER BY date DESC
            LIMIT ?
        ''', (limit,))
        
        return [dict(row) for row in cursor.fetchall()]

def get_entries_by_date(date=None):
    """Get all entries for a specific date (defaults to today)"""
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, date, food_items, total_calories, analysis_text, timestamp
            FROM calorie_entries
            WHERE date = ?
            ORDER BY timestamp DESC
        ''', (date,))
        
        return [dict(row) for row in cursor.fetchall()]

def get_weekly_summary():
    """Get a summary of the last 7 days"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                date,
                total_calories,
                entry_count
            FROM daily_totals
            WHERE date >= date('now', '-7 days')
            ORDER BY date DESC
        ''')
        
        return [dict(row) for row in cursor.fetchall()]

def delete_entry(entry_id):
    """Delete a specific entry and update daily totals"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get entry details before deleting
        cursor.execute('''
            SELECT date, total_calories FROM calorie_entries WHERE id = ?
        ''', (entry_id,))
        entry = cursor.fetchone()
        
        if not entry:
            return False
        
        date, calories = entry
        
        # Delete the entry
        cursor.execute('DELETE FROM calorie_entries WHERE id = ?', (entry_id,))
        
        # Update daily total
        cursor.execute('''
            UPDATE daily_totals
            SET total_calories = total_calories - ?,
                entry_count = entry_count - 1,
                last_updated = CURRENT_TIMESTAMP
            WHERE date = ?
        ''', (calories, date))
        
        # If no more entries for this day, delete the daily total
        cursor.execute('''
            DELETE FROM daily_totals
            WHERE date = ? AND entry_count <= 0
        ''', (date,))
        
        return True

def clear_all_data():
    """Clear all data from the database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM calorie_entries')
        cursor.execute('DELETE FROM daily_totals')
        return True

if __name__ == '__main__':
    # Initialize database when run directly
    init_db()
    print("Database setup complete!")
