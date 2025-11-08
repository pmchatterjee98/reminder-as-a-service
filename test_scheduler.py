import pytest
from unittest.mock import Mock, patch, MagicMock
import os
from datetime import datetime, timedelta
import database
import scheduler

TEST_DB = "test_scheduler_todos.db"

@pytest.fixture(autouse=True)
def setup_test_db():
    """Setup test database before each test."""
    original_db = database.DB_NAME
    database.DB_NAME = TEST_DB
    
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    
    database.init_db()
    
    yield
    
    database.DB_NAME = original_db
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

class TestCheckUpcomingTodos:
    @patch('scheduler.notifications.send_all_reminders')
    def test_check_upcoming_todos_no_todos(self, mock_send):
        """Test checking with no todos."""
        scheduler.check_upcoming_todos()
        mock_send.assert_not_called()
    
    @patch('scheduler.notifications.send_all_reminders')
    @patch('scheduler.database.mark_reminder_sent')
    def test_check_upcoming_todos_sends_reminders(self, mock_mark_sent, mock_send):
        """Test that reminders are sent for upcoming todos."""
        now = datetime.now()
        due_soon = now + timedelta(hours=2)
        
        todo_id = database.add_todo(
            "Upcoming Task",
            "Description",
            due_soon.strftime("%Y-%m-%d %H:%M:%S"),
            email="test@example.com",
            reminder_hours=3
        )
        
        mock_send.return_value = None
        
        scheduler.check_upcoming_todos()
        
        assert mock_send.call_count >= 1
        mock_mark_sent.assert_called_with(todo_id)
    
    @patch('scheduler.notifications.send_all_reminders')
    def test_check_upcoming_todos_skips_completed(self, mock_send):
        """Test that completed todos don't trigger reminders."""
        now = datetime.now()
        due_soon = now + timedelta(hours=2)
        
        todo_id = database.add_todo(
            "Completed Task",
            "",
            due_soon.strftime("%Y-%m-%d %H:%M:%S"),
            email="test@example.com",
            reminder_hours=3
        )
        
        database.toggle_complete(todo_id)
        
        scheduler.check_upcoming_todos()
        
        mock_send.assert_not_called()
    
    @patch('scheduler.notifications.send_all_reminders')
    def test_check_upcoming_todos_skips_already_sent(self, mock_send):
        """Test that todos with reminders already sent are skipped."""
        now = datetime.now()
        due_soon = now + timedelta(hours=2)
        
        todo_id = database.add_todo(
            "Already Reminded",
            "",
            due_soon.strftime("%Y-%m-%d %H:%M:%S"),
            email="test@example.com",
            reminder_hours=3
        )
        
        database.mark_reminder_sent(todo_id)
        
        scheduler.check_upcoming_todos()
        
        mock_send.assert_not_called()
    
    @patch('scheduler.notifications.send_all_reminders')
    def test_check_upcoming_todos_respects_reminder_hours(self, mock_send):
        """Test that reminder_hours setting is respected."""
        now = datetime.now()
        due_far = now + timedelta(hours=50)
        
        database.add_todo(
            "Far Future Task",
            "",
            due_far.strftime("%Y-%m-%d %H:%M:%S"),
            email="test@example.com",
            reminder_hours=24
        )
        
        scheduler.check_upcoming_todos()
        
        mock_send.assert_not_called()

class TestSchedulerStartStop:
    def test_start_scheduler_creates_scheduler(self):
        """Test that start_scheduler creates a scheduler instance."""
        scheduler.start_scheduler()
        assert scheduler.reminder_scheduler is not None
    
    def test_stop_scheduler_shuts_down(self):
        """Test that stop_scheduler shuts down the scheduler."""
        scheduler.start_scheduler()
        scheduler.stop_scheduler()
