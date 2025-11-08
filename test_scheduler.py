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

class TestCheckAndSendReminders:
    @patch('scheduler.notifications.send_email_reminder')
    @patch('scheduler.notifications.send_sms_reminder')
    @patch('scheduler.notifications.send_whatsapp_reminder')
    def test_check_and_send_no_todos(self, mock_whatsapp, mock_sms, mock_email):
        """Test checking with no todos."""
        scheduler.check_and_send_reminders()
        mock_email.assert_not_called()
        mock_sms.assert_not_called()
        mock_whatsapp.assert_not_called()
    
    @patch('scheduler.notifications.send_email_reminder')
    @patch('scheduler.database.mark_reminder_sent')
    def test_check_and_send_sends_reminders(self, mock_mark_sent, mock_email):
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
        
        mock_email.return_value = True
        
        scheduler.check_and_send_reminders()
        
        mock_email.assert_called_once()
        mock_mark_sent.assert_called_with(todo_id)
    
    @patch('scheduler.notifications.send_email_reminder')
    def test_check_and_send_skips_completed(self, mock_email):
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
        
        scheduler.check_and_send_reminders()
        
        mock_email.assert_not_called()
    
    @patch('scheduler.notifications.send_email_reminder')
    def test_check_and_send_skips_already_sent(self, mock_email):
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
        
        scheduler.check_and_send_reminders()
        
        mock_email.assert_not_called()
    
    @patch('scheduler.notifications.send_email_reminder')
    def test_check_and_send_respects_reminder_hours(self, mock_email):
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
        
        scheduler.check_and_send_reminders()
        
        mock_email.assert_not_called()

class TestSchedulerStartStop:
    def test_start_scheduler_creates_scheduler(self):
        """Test that start_scheduler creates a scheduler instance."""
        scheduler.start_scheduler()
        assert scheduler.scheduler is not None
        scheduler.stop_scheduler()
    
    def test_stop_scheduler_shuts_down(self):
        """Test that stop_scheduler shuts down the scheduler."""
        scheduler.start_scheduler()
        scheduler.stop_scheduler()
        assert not scheduler.scheduler.running
