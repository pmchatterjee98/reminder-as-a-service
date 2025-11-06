import sqlite3
from datetime import datetime
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
            reminder_sent INTEGER DEFAULT 0
        )
    ''')
    
    conn.commit()
    conn.close()

def add_todo(title: str, description: str, due_date: str, email: str = "", phone: str = "") -> int:
    """Add a new todo to the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Normalize due_date to SQLite format (replace 'T' with space)
    normalized_due_date = due_date.replace('T', ' ')
    
    cursor.execute('''
        INSERT INTO todos (title, description, due_date, email, phone)
        VALUES (?, ?, ?, ?, ?)
    ''', (title, description, normalized_due_date, email, phone))
    
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

def update_todo(todo_id: int, title: str, description: str, due_date: str, email: str = "", phone: str = ""):
    """Update an existing todo."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Normalize due_date to SQLite format (replace 'T' with space)
    normalized_due_date = due_date.replace('T', ' ')
    
    cursor.execute('''
        UPDATE todos
        SET title = ?, description = ?, due_date = ?, email = ?, phone = ?
        WHERE id = ?
    ''', (title, description, normalized_due_date, email, phone, todo_id))
    
    conn.commit()
    conn.close()

def toggle_complete(todo_id: int):
    """Toggle the completion status of a todo."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT completed FROM todos WHERE id = ?', (todo_id,))
    current_status = cursor.fetchone()[0]
    new_status = 0 if current_status else 1
    
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

def get_upcoming_todos(hours_ahead: int = 24) -> List[Dict]:
    """Get todos that are due within the specified hours and haven't had reminders sent."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    now = datetime.now()
    future = datetime.fromtimestamp(now.timestamp() + hours_ahead * 3600)
    
    # Format datetime strings to match SQLite storage format (without 'T' separator)
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    future_str = future.strftime('%Y-%m-%d %H:%M:%S')
    
    # Normalize due_date in the query to handle both 'T' and space separators
    cursor.execute('''
        SELECT * FROM todos
        WHERE completed = 0
        AND reminder_sent = 0
        AND REPLACE(due_date, 'T', ' ') <= ?
        AND REPLACE(due_date, 'T', ' ') > ?
    ''', (future_str, now_str))
    
    rows = cursor.fetchall()
    todos = [dict(row) for row in rows]
    conn.close()
    return todos

def mark_reminder_sent(todo_id: int):
    """Mark that a reminder has been sent for this todo."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('UPDATE todos SET reminder_sent = 1 WHERE id = ?', (todo_id,))
    
    conn.commit()
    conn.close()
