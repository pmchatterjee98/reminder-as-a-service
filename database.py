import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional

DB_NAME = "todos.db"

def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            due_date TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            email TEXT,
            phone TEXT,
            reminder_sent INTEGER DEFAULT 0,
            reminder_hours INTEGER DEFAULT 24,
            is_recurring INTEGER DEFAULT 0,
            recurrence_frequency TEXT,
            recurrence_interval INTEGER,
            category TEXT,
            priority TEXT DEFAULT 'Medium'
        )
    ''')
    
    # Migration: Add reminder_hours column if it doesn't exist
    try:
        cursor.execute("SELECT reminder_hours FROM todos LIMIT 1")
    except sqlite3.OperationalError:
        print("Migrating database: Adding reminder_hours column...")
        cursor.execute("ALTER TABLE todos ADD COLUMN reminder_hours INTEGER DEFAULT 24")
        print("Migration complete.")
    
    # Migration: Add recurring task columns if they don't exist
    try:
        cursor.execute("SELECT is_recurring FROM todos LIMIT 1")
    except sqlite3.OperationalError:
        print("Migrating database: Adding recurring task columns...")
        cursor.execute("ALTER TABLE todos ADD COLUMN is_recurring INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE todos ADD COLUMN recurrence_frequency TEXT")
        cursor.execute("ALTER TABLE todos ADD COLUMN recurrence_interval INTEGER")
        print("Migration complete.")
    
    # Migration: Add category and priority columns if they don't exist
    try:
        cursor.execute("SELECT category FROM todos LIMIT 1")
    except sqlite3.OperationalError:
        print("Migrating database: Adding category and priority columns...")
        cursor.execute("ALTER TABLE todos ADD COLUMN category TEXT")
        cursor.execute("ALTER TABLE todos ADD COLUMN priority TEXT DEFAULT 'Medium'")
        print("Migration complete.")
    
    conn.commit()
    conn.close()

def add_todo(title: str, description: str, due_date: str, email: str = "", phone: str = "", reminder_hours: int = 24, 
             is_recurring: bool = False, recurrence_frequency: Optional[str] = None, recurrence_interval: Optional[int] = None,
             category: Optional[str] = None, priority: str = "Medium") -> int:
    """Add a new todo to the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Normalize due_date to SQLite format (replace 'T' with space)
    normalized_due_date = due_date.replace('T', ' ')
    
    cursor.execute('''
        INSERT INTO todos (title, description, due_date, email, phone, reminder_hours, 
                          is_recurring, recurrence_frequency, recurrence_interval, category, priority)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (title, description, normalized_due_date, email, phone, reminder_hours,
          1 if is_recurring else 0, recurrence_frequency, recurrence_interval, category, priority))
    
    todo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return todo_id if todo_id is not None else 0

def get_all_todos() -> List[Dict]:
    """Get all todos from the database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM todos ORDER BY due_date ASC, id DESC')
    rows = cursor.fetchall()
    
    todos = [dict(row) for row in rows]
    conn.close()
    return todos

def get_todo_by_id(todo_id: int) -> Optional[Dict]:
    """Get a specific todo by ID."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM todos WHERE id = ?', (todo_id,))
    row = cursor.fetchone()
    
    todo = dict(row) if row else None
    conn.close()
    return todo

def update_todo(todo_id: int, title: str, description: str, due_date: str, email: str = "", phone: str = "", reminder_hours: int = 24,
               is_recurring: bool = False, recurrence_frequency: Optional[str] = None, recurrence_interval: Optional[int] = None,
               category: Optional[str] = None, priority: str = "Medium"):
    """Update an existing todo."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Normalize due_date to SQLite format (replace 'T' with space)
    normalized_due_date = due_date.replace('T', ' ')
    
    cursor.execute('''
        UPDATE todos
        SET title = ?, description = ?, due_date = ?, email = ?, phone = ?, reminder_hours = ?,
            is_recurring = ?, recurrence_frequency = ?, recurrence_interval = ?, category = ?, priority = ?
        WHERE id = ?
    ''', (title, description, normalized_due_date, email, phone, reminder_hours,
          1 if is_recurring else 0, recurrence_frequency, recurrence_interval, category, priority, todo_id))
    
    conn.commit()
    conn.close()

def toggle_complete(todo_id: int):
    """Toggle the completion status of a todo. For recurring tasks, reschedule instead of marking complete."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM todos WHERE id = ?', (todo_id,))
    todo = dict(cursor.fetchone())
    current_status = todo['completed']
    new_status = 0 if current_status else 1
    
    # If completing a recurring task, reschedule it instead
    if new_status == 1 and todo.get('is_recurring'):
        # Parse the current due date
        due_date_str = todo['due_date'].replace(' ', 'T') if ' ' in todo['due_date'] else todo['due_date']
        current_due_date = datetime.fromisoformat(due_date_str)
        
        # Calculate next due date based on recurrence settings
        frequency = todo.get('recurrence_frequency', 'days')
        interval = todo.get('recurrence_interval', 1)
        
        if frequency == 'days':
            next_due_date = current_due_date + timedelta(days=interval)
        elif frequency == 'weeks':
            next_due_date = current_due_date + timedelta(weeks=interval)
        elif frequency == 'months':
            # Approximate months as 30 days
            next_due_date = current_due_date + timedelta(days=30 * interval)
        elif frequency == 'years':
            # Approximate years as 365 days
            next_due_date = current_due_date + timedelta(days=365 * interval)
        else:
            next_due_date = current_due_date + timedelta(days=interval)
        
        # Update the due date and reset reminder_sent
        normalized_due_date = next_due_date.strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('UPDATE todos SET due_date = ?, reminder_sent = 0 WHERE id = ?', 
                      (normalized_due_date, todo_id))
    else:
        # Regular toggle for non-recurring tasks
        cursor.execute('UPDATE todos SET completed = ? WHERE id = ?', (new_status, todo_id))
    
    conn.commit()
    conn.close()

def delete_todo(todo_id: int):
    """Delete a todo from the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
    
    conn.commit()
    conn.close()

def get_upcoming_todos() -> List[Dict]:
    """Get todos that need reminders sent based on their individual reminder_hours setting."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    now = datetime.now()
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    
    # Get all incomplete todos that haven't had reminders sent
    # We'll filter by individual reminder_hours in Python since SQLite doesn't support datetime arithmetic well
    cursor.execute('''
        SELECT * FROM todos
        WHERE completed = 0
        AND reminder_sent = 0
        AND REPLACE(due_date, 'T', ' ') > ?
    ''', (now_str,))
    
    rows = cursor.fetchall()
    todos = []
    
    for row in rows:
        todo = dict(row)
        # Parse the due date
        due_date_str = todo['due_date'].replace(' ', 'T') if ' ' in todo['due_date'] else todo['due_date']
        due_date = datetime.fromisoformat(due_date_str)
        
        # Calculate when reminder should be sent
        reminder_hours = todo.get('reminder_hours', 24)
        time_until_due = (due_date - now).total_seconds() / 3600  # hours
        
        # Send reminder if we're within the reminder window
        if 0 < time_until_due <= reminder_hours:
            todos.append(todo)
    
    conn.close()
    return todos

def mark_reminder_sent(todo_id: int):
    """Mark that a reminder has been sent for this todo."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('UPDATE todos SET reminder_sent = 1 WHERE id = ?', (todo_id,))
    
    conn.commit()
    conn.close()
