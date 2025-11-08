"""
Multi-user database operations for RAAS.
Wraps existing database functions with user-id awareness and authorization.
"""

import sqlite3
from typing import List, Dict, Optional
from datetime import datetime
import database

DB_NAME = database.DB_NAME


def add_todo_for_user(user_id: str, title: str, description: str, due_date: str,
                      email: str = "", phone: str = "", whatsapp_phone: str = "",
                      reminder_hours: int = 24,
                      is_recurring: bool = False, recurrence_frequency: Optional[str] = None,
                      recurrence_interval: Optional[int] = None, category: Optional[str] = None,
                      priority: str = "Medium") -> int:
    """
    Add a todo for a specific user.
    
    Args:
        user_id: User's ID
        (other args same as database.add_todo)
    
    Returns:
        Todo ID if successful, -1 otherwise
    """
    # Add the todo using existing function
    todo_id = database.add_todo(
        title=title,
        description=description,
        due_date=due_date,
        email=email,
        phone=phone,
        whatsapp_phone=whatsapp_phone,
        reminder_hours=reminder_hours,
        is_recurring=is_recurring,
        recurrence_frequency=recurrence_frequency,
        recurrence_interval=recurrence_interval,
        category=category,
        priority=priority
    )
    
    if todo_id == -1:
        return -1
    
    # Update the todo with user_id
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE todos SET user_id = ? WHERE id = ?
        ''', (user_id, todo_id))
        conn.commit()
        return todo_id
    except Exception as e:
        print(f"Error setting user_id for todo {todo_id}: {e}")
        return -1
    finally:
        conn.close()


def get_todos_for_user(user_id: str) -> List[Dict]:
    """
    Get all todos for a specific user.
    
    Args:
        user_id: User's ID
    
    Returns:
        List of todos belonging to the user
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM todos 
        WHERE user_id = ?
        ORDER BY due_date ASC
    ''', (user_id,))
    
    todos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return todos


def get_todo_by_id_for_user(todo_id: int, user_id: str) -> Optional[Dict]:
    """
    Get a todo by ID, verifying it belongs to the user.
    
    Args:
        todo_id: Todo's ID
        user_id: User's ID (for authorization)
    
    Returns:
        Todo dictionary if found and belongs to user, None otherwise
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM todos 
        WHERE id = ? AND user_id = ?
    ''', (todo_id, user_id))
    
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


def update_todo_for_user(user_id: str, todo_id: int, title: str, description: str,
                         due_date: str, email: str = "", phone: str = "",
                         whatsapp_phone: str = "", reminder_hours: int = 24,
                         is_recurring: bool = False, recurrence_frequency: Optional[str] = None,
                         recurrence_interval: Optional[int] = None, category: Optional[str] = None,
                         priority: str = "Medium") -> bool:
    """
    Update a todo, verifying it belongs to the user.
    
    Args:
        user_id: User's ID (for authorization)
        todo_id: Todo's ID
        (other args same as database.update_todo)
    
    Returns:
        True if successful, False otherwise
    """
    # Verify ownership
    todo = get_todo_by_id_for_user(todo_id, user_id)
    if not todo:
        print(f"Todo {todo_id} not found or doesn't belong to user {user_id}")
        return False
    
    # Update using existing function
    return database.update_todo(
        todo_id=todo_id,
        title=title,
        description=description,
        due_date=due_date,
        email=email,
        phone=phone,
        whatsapp_phone=whatsapp_phone,
        reminder_hours=reminder_hours,
        is_recurring=is_recurring,
        recurrence_frequency=recurrence_frequency,
        recurrence_interval=recurrence_interval,
        category=category,
        priority=priority
    )


def toggle_complete_for_user(todo_id: int, user_id: str) -> bool:
    """
    Toggle todo completion status, verifying it belongs to the user.
    
    Args:
        todo_id: Todo's ID
        user_id: User's ID (for authorization)
    
    Returns:
        True if successful, False otherwise
    """
    # Verify ownership
    todo = get_todo_by_id_for_user(todo_id, user_id)
    if not todo:
        return False
    
    return database.toggle_complete(todo_id)


def delete_todo_for_user(todo_id: int, user_id: str) -> bool:
    """
    Delete a todo, verifying it belongs to the user.
    
    Args:
        todo_id: Todo's ID
        user_id: User's ID (for authorization)
    
    Returns:
        True if successful, False otherwise
    """
    # Verify ownership
    todo = get_todo_by_id_for_user(todo_id, user_id)
    if not todo:
        return False
    
    return database.delete_todo(todo_id)


def delete_completed_tasks_for_user(user_id: str) -> int:
    """
    Delete all completed tasks for a user.
    
    Args:
        user_id: User's ID
    
    Returns:
        Number of tasks deleted
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        DELETE FROM todos 
        WHERE completed = 1 AND user_id = ?
    ''', (user_id,))
    
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    
    return deleted_count


def get_upcoming_todos_for_user(user_id: str) -> List[Dict]:
    """
    Get todos with upcoming deadlines for a user (for reminder system).
    
    Args:
        user_id: User's ID
    
    Returns:
        List of upcoming todos for the user
    """
    # Get all upcoming todos
    all_upcoming = database.get_upcoming_todos()
    
    # Filter by user_id - strict ownership check
    user_upcoming = [
        todo for todo in all_upcoming 
        if todo.get('user_id') == user_id
    ]
    
    return user_upcoming


def get_user_statistics(user_id: str) -> Dict:
    """
    Get statistics about a user's todos.
    
    Args:
        user_id: User's ID
    
    Returns:
        Dictionary with statistics
    """
    todos = get_todos_for_user(user_id)
    
    total = len(todos)
    completed = sum(1 for todo in todos if todo.get('completed', 0) == 1)
    pending = total - completed
    
    # Count by priority
    high_priority = sum(1 for todo in todos if todo.get('priority') == 'High' and not todo.get('completed'))
    medium_priority = sum(1 for todo in todos if todo.get('priority') == 'Medium' and not todo.get('completed'))
    low_priority = sum(1 for todo in todos if todo.get('priority') == 'Low' and not todo.get('completed'))
    
    # Count overdue
    now = datetime.now()
    overdue = 0
    for todo in todos:
        if not todo.get('completed'):
            try:
                due_date = datetime.fromisoformat(todo['due_date'])
                if due_date < now:
                    overdue += 1
            except:
                pass
    
    return {
        'total': total,
        'completed': completed,
        'pending': pending,
        'high_priority': high_priority,
        'medium_priority': medium_priority,
        'low_priority': low_priority,
        'overdue': overdue
    }
