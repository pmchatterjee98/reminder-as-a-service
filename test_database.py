import pytest
import os
import sqlite3
from datetime import datetime, timedelta
import database

TEST_DB = "test_todos.db"

@pytest.fixture(autouse=True)
def setup_test_db():
    """Setup test database before each test and clean up after."""
    original_db = database.DB_NAME
    database.DB_NAME = TEST_DB
    
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    
    database.init_db()
    
    yield
    
    database.DB_NAME = original_db
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

class TestDatabaseInit:
    def test_init_db_creates_tables(self):
        """Test that database initialization creates the todos table."""
        conn = sqlite3.connect(TEST_DB)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='todos'")
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == 'todos'
        conn.close()
    
    def test_init_db_has_all_columns(self):
        """Test that todos table has all required columns."""
        conn = sqlite3.connect(TEST_DB)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(todos)")
        columns = {row[1] for row in cursor.fetchall()}
        
        required_columns = {
            'id', 'title', 'description', 'due_date', 'completed',
            'created_at', 'email', 'phone', 'whatsapp_phone', 'reminder_sent',
            'reminder_hours', 'is_recurring', 'recurrence_frequency',
            'recurrence_interval', 'category', 'priority'
        }
        
        assert required_columns.issubset(columns)
        conn.close()

class TestAddTodo:
    def test_add_todo_basic(self):
        """Test adding a basic todo."""
        todo_id = database.add_todo(
            title="Test Task",
            description="Test Description",
            due_date="2025-12-01 10:00:00"
        )
        
        assert todo_id > 0
        
        todo = database.get_todo_by_id(todo_id)
        assert todo is not None
        assert todo['title'] == "Test Task"
        assert todo['description'] == "Test Description"
        assert todo['completed'] == 0
    
    def test_add_todo_with_all_fields(self):
        """Test adding a todo with all fields."""
        todo_id = database.add_todo(
            title="Complete Task",
            description="Full description",
            due_date="2025-12-01 10:00:00",
            email="test@example.com",
            phone="+1234567890",
            whatsapp_phone="+1234567890",
            reminder_hours=48,
            is_recurring=True,
            recurrence_frequency="weeks",
            recurrence_interval=2,
            category="Work",
            priority="High"
        )
        
        todo = database.get_todo_by_id(todo_id)
        assert todo['email'] == "test@example.com"
        assert todo['phone'] == "+1234567890"
        assert todo['whatsapp_phone'] == "+1234567890"
        assert todo['reminder_hours'] == 48
        assert todo['is_recurring'] == 1
        assert todo['recurrence_frequency'] == "weeks"
        assert todo['recurrence_interval'] == 2
        assert todo['category'] == "Work"
        assert todo['priority'] == "High"
    
    def test_add_todo_normalizes_date(self):
        """Test that ISO format dates with 'T' are normalized to spaces."""
        todo_id = database.add_todo(
            title="Date Test",
            description="",
            due_date="2025-12-01T10:00:00"
        )
        
        todo = database.get_todo_by_id(todo_id)
        assert ' ' in todo['due_date']
        assert 'T' not in todo['due_date']

class TestGetTodos:
    def test_get_all_todos_empty(self):
        """Test getting todos from empty database."""
        todos = database.get_all_todos()
        assert todos == []
    
    def test_get_all_todos_multiple(self):
        """Test getting multiple todos."""
        database.add_todo("Task 1", "", "2025-12-01 10:00:00")
        database.add_todo("Task 2", "", "2025-12-02 10:00:00")
        database.add_todo("Task 3", "", "2025-12-03 10:00:00")
        
        todos = database.get_all_todos()
        assert len(todos) == 3
        assert todos[0]['title'] == "Task 1"
    
    def test_get_todo_by_id_exists(self):
        """Test getting a specific todo by ID."""
        todo_id = database.add_todo("Test Task", "", "2025-12-01 10:00:00")
        
        todo = database.get_todo_by_id(todo_id)
        assert todo is not None
        assert todo['id'] == todo_id
        assert todo['title'] == "Test Task"
    
    def test_get_todo_by_id_not_exists(self):
        """Test getting a non-existent todo."""
        todo = database.get_todo_by_id(99999)
        assert todo is None

class TestUpdateTodo:
    def test_update_todo_all_fields(self):
        """Test updating all fields of a todo."""
        todo_id = database.add_todo(
            "Original Title",
            "Original Desc",
            "2025-12-01 10:00:00"
        )
        
        database.update_todo(
            todo_id=todo_id,
            title="Updated Title",
            description="Updated Desc",
            due_date="2025-12-02 15:00:00",
            email="updated@example.com",
            phone="+9876543210",
            whatsapp_phone="+9876543210",
            reminder_hours=72,
            is_recurring=True,
            recurrence_frequency="days",
            recurrence_interval=5,
            category="Personal",
            priority="Low"
        )
        
        todo = database.get_todo_by_id(todo_id)
        assert todo['title'] == "Updated Title"
        assert todo['description'] == "Updated Desc"
        assert "2025-12-02" in todo['due_date']
        assert todo['email'] == "updated@example.com"
        assert todo['category'] == "Personal"
        assert todo['priority'] == "Low"

class TestToggleComplete:
    def test_toggle_complete_to_done(self):
        """Test marking a todo as complete."""
        todo_id = database.add_todo("Task", "", "2025-12-01 10:00:00")
        
        database.toggle_complete(todo_id)
        
        todo = database.get_todo_by_id(todo_id)
        assert todo['completed'] == 1
    
    def test_toggle_complete_back_to_pending(self):
        """Test unmarking a completed todo."""
        todo_id = database.add_todo("Task", "", "2025-12-01 10:00:00")
        
        database.toggle_complete(todo_id)
        database.toggle_complete(todo_id)
        
        todo = database.get_todo_by_id(todo_id)
        assert todo['completed'] == 0
    
    def test_toggle_complete_recurring_reschedules_daily(self):
        """Test that completing a recurring task reschedules it (daily)."""
        due_date = datetime.now() + timedelta(days=1)
        todo_id = database.add_todo(
            "Recurring Task",
            "",
            due_date.strftime("%Y-%m-%d %H:%M:%S"),
            is_recurring=True,
            recurrence_frequency="days",
            recurrence_interval=1
        )
        
        original_due = database.get_todo_by_id(todo_id)['due_date']
        
        database.toggle_complete(todo_id)
        
        todo = database.get_todo_by_id(todo_id)
        assert todo['completed'] == 0
        assert todo['due_date'] != original_due
        assert todo['reminder_sent'] == 0
    
    def test_toggle_complete_recurring_reschedules_weekly(self):
        """Test that completing a recurring task reschedules it (weekly)."""
        due_date = datetime.now() + timedelta(days=1)
        todo_id = database.add_todo(
            "Weekly Task",
            "",
            due_date.strftime("%Y-%m-%d %H:%M:%S"),
            is_recurring=True,
            recurrence_frequency="weeks",
            recurrence_interval=2
        )
        
        database.toggle_complete(todo_id)
        
        todo = database.get_todo_by_id(todo_id)
        assert todo['completed'] == 0

class TestDeleteTodo:
    def test_delete_todo_removes_from_db(self):
        """Test that deleting a todo removes it from database."""
        todo_id = database.add_todo("Task", "", "2025-12-01 10:00:00")
        
        database.delete_todo(todo_id)
        
        todo = database.get_todo_by_id(todo_id)
        assert todo is None
    
    def test_delete_todo_affects_count(self):
        """Test that deleting affects total count."""
        database.add_todo("Task 1", "", "2025-12-01 10:00:00")
        todo_id_2 = database.add_todo("Task 2", "", "2025-12-02 10:00:00")
        database.add_todo("Task 3", "", "2025-12-03 10:00:00")
        
        database.delete_todo(todo_id_2)
        
        todos = database.get_all_todos()
        assert len(todos) == 2

class TestGetUpcomingTodos:
    def test_get_upcoming_todos_empty(self):
        """Test getting upcoming todos from empty database."""
        upcoming = database.get_upcoming_todos()
        assert upcoming == []
    
    def test_get_upcoming_todos_within_24_hours(self):
        """Test that todos within 24 hours are included (automatic reminder)."""
        now = datetime.now()
        
        # Task due in 12 hours - should be included
        due_12h = now + timedelta(hours=12)
        todo_id = database.add_todo(
            "Task due in 12 hours",
            "",
            due_12h.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        upcoming = database.get_upcoming_todos()
        assert len(upcoming) == 1
        assert upcoming[0]['id'] == todo_id
    
    def test_get_upcoming_todos_beyond_24_hours(self):
        """Test that todos beyond 24 hours are not included."""
        now = datetime.now()
        
        # Task due in 25 hours - should NOT be included
        due_25h = now + timedelta(hours=25)
        database.add_todo(
            "Task due in 25 hours",
            "",
            due_25h.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        upcoming = database.get_upcoming_todos()
        assert len(upcoming) == 0
    
    def test_get_upcoming_todos_exactly_24_hours(self):
        """Test that todos exactly 24 hours away are included."""
        now = datetime.now()
        
        # Task due in exactly 24 hours
        due_24h = now + timedelta(hours=24)
        todo_id = database.add_todo(
            "Task due in 24 hours",
            "",
            due_24h.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        upcoming = database.get_upcoming_todos()
        assert len(upcoming) == 1
        assert upcoming[0]['id'] == todo_id
    
    def test_get_upcoming_todos_filters_completed(self):
        """Test that completed todos are not in upcoming."""
        now = datetime.now()
        future = now + timedelta(hours=2)
        
        todo_id = database.add_todo(
            "Test Task",
            "",
            future.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        database.toggle_complete(todo_id)
        
        upcoming = database.get_upcoming_todos()
        assert len(upcoming) == 0
    
    def test_get_upcoming_todos_filters_already_sent(self):
        """Test that todos with reminders already sent are not included."""
        now = datetime.now()
        future = now + timedelta(hours=2)
        
        todo_id = database.add_todo(
            "Test Task",
            "",
            future.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        database.mark_reminder_sent(todo_id)
        
        upcoming = database.get_upcoming_todos()
        assert len(upcoming) == 0
    
    def test_get_upcoming_todos_multiple_within_window(self):
        """Test that multiple todos within 24 hours are all included."""
        now = datetime.now()
        
        # Add 3 tasks within 24 hours
        todo_id1 = database.add_todo("Task 1", "", (now + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"))
        todo_id2 = database.add_todo("Task 2", "", (now + timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S"))
        todo_id3 = database.add_todo("Task 3", "", (now + timedelta(hours=23)).strftime("%Y-%m-%d %H:%M:%S"))
        
        # Add 1 task beyond 24 hours
        database.add_todo("Task 4", "", (now + timedelta(hours=30)).strftime("%Y-%m-%d %H:%M:%S"))
        
        upcoming = database.get_upcoming_todos()
        assert len(upcoming) == 3
        todo_ids = [t['id'] for t in upcoming]
        assert todo_id1 in todo_ids
        assert todo_id2 in todo_ids
        assert todo_id3 in todo_ids

class TestMarkReminderSent:
    def test_mark_reminder_sent(self):
        """Test marking a reminder as sent."""
        todo_id = database.add_todo("Task", "", "2025-12-01 10:00:00")
        
        database.mark_reminder_sent(todo_id)
        
        todo = database.get_todo_by_id(todo_id)
        assert todo['reminder_sent'] == 1

class TestDeleteCompletedTasks:
    def test_delete_completed_tasks_none_completed(self):
        """Test deleting completed tasks when none are completed."""
        # Add some incomplete tasks
        database.add_todo("Task 1", "", "2025-12-01 10:00:00")
        database.add_todo("Task 2", "", "2025-12-02 10:00:00")
        
        # Delete completed tasks
        deleted_count = database.delete_completed_tasks()
        
        # Verify no tasks were deleted
        assert deleted_count == 0
        todos = database.get_all_todos()
        assert len(todos) == 2
    
    def test_delete_completed_tasks_some_completed(self):
        """Test deleting completed tasks when some are completed."""
        # Add tasks
        todo_id1 = database.add_todo("Task 1", "", "2025-12-01 10:00:00")
        todo_id2 = database.add_todo("Task 2", "", "2025-12-02 10:00:00")
        todo_id3 = database.add_todo("Task 3", "", "2025-12-03 10:00:00")
        
        # Complete two tasks
        database.toggle_complete(todo_id1)
        database.toggle_complete(todo_id3)
        
        # Delete completed tasks
        deleted_count = database.delete_completed_tasks()
        
        # Verify 2 tasks were deleted
        assert deleted_count == 2
        todos = database.get_all_todos()
        assert len(todos) == 1
        assert todos[0]['id'] == todo_id2
    
    def test_delete_completed_tasks_all_completed(self):
        """Test deleting completed tasks when all are completed."""
        # Add tasks
        todo_id1 = database.add_todo("Task 1", "", "2025-12-01 10:00:00")
        todo_id2 = database.add_todo("Task 2", "", "2025-12-02 10:00:00")
        
        # Complete all tasks
        database.toggle_complete(todo_id1)
        database.toggle_complete(todo_id2)
        
        # Delete completed tasks
        deleted_count = database.delete_completed_tasks()
        
        # Verify all tasks were deleted
        assert deleted_count == 2
        todos = database.get_all_todos()
        assert len(todos) == 0
    
    def test_delete_completed_tasks_preserves_incomplete(self):
        """Test that delete_completed_tasks preserves incomplete tasks."""
        # Add and complete one task
        todo_id1 = database.add_todo("Completed Task", "", "2025-12-01 10:00:00")
        database.toggle_complete(todo_id1)
        
        # Add incomplete tasks
        todo_id2 = database.add_todo("Incomplete Task 1", "", "2025-12-02 10:00:00")
        todo_id3 = database.add_todo("Incomplete Task 2", "", "2025-12-03 10:00:00")
        
        # Delete completed tasks
        deleted_count = database.delete_completed_tasks()
        
        # Verify only completed task was deleted
        assert deleted_count == 1
        todos = database.get_all_todos()
        assert len(todos) == 2
        todo_ids = [t['id'] for t in todos]
        assert todo_id2 in todo_ids
        assert todo_id3 in todo_ids
        assert todo_id1 not in todo_ids
