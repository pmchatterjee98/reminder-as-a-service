import pytest
from unittest.mock import Mock, patch, MagicMock
import notifications
from datetime import datetime

class TestEmailNotifications:
    @patch('smtplib.SMTP')
    @patch('os.getenv')
    def test_send_email_success(self, mock_getenv, mock_smtp):
        """Test successful email sending."""
        mock_getenv.side_effect = lambda key: {
            'SENDER_EMAIL': 'test@example.com',
            'SENDER_PASSWORD': 'password123'
        }.get(key)
        
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = notifications.send_email_reminder(
            to_email="user@example.com",
            todo_title="Test Task",
            due_date="2025-12-01 10:00:00"
        )
        
        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with('test@example.com', 'password123')
        mock_server.send_message.assert_called_once()
    
    @patch('smtplib.SMTP')
    @patch('os.getenv')
    def test_send_email_no_recipient(self, mock_getenv, mock_smtp):
        """Test email with no recipient returns False."""
        result = notifications.send_email_reminder(
            to_email="",
            todo_title="Test Task",
            due_date="2025-12-01 10:00:00"
        )
        
        assert result is False
        mock_smtp.assert_not_called()
    
    @patch('smtplib.SMTP')
    @patch('os.getenv')
    def test_send_email_no_credentials(self, mock_getenv, mock_smtp):
        """Test email with no credentials returns False."""
        mock_getenv.return_value = None
        
        result = notifications.send_email_reminder(
            to_email="user@example.com",
            todo_title="Test Task",
            due_date="2025-12-01 10:00:00"
        )
        
        assert result is False
    
    @patch('smtplib.SMTP')
    @patch('os.getenv')
    def test_send_email_smtp_error(self, mock_getenv, mock_smtp):
        """Test email sending handles SMTP errors gracefully."""
        mock_getenv.side_effect = lambda key: {
            'SENDER_EMAIL': 'test@example.com',
            'SENDER_PASSWORD': 'password123'
        }.get(key)
        
        mock_smtp.return_value.__enter__.side_effect = Exception("SMTP Error")
        
        result = notifications.send_email_reminder(
            to_email="user@example.com",
            todo_title="Test Task",
            due_date="2025-12-01 10:00:00"
        )
        
        assert result is False
    
    @patch('smtplib.SMTP')
    @patch('os.getenv')
    def test_email_content_formatting(self, mock_getenv, mock_smtp):
        """Test that email content is properly formatted with RAAS branding."""
        mock_getenv.side_effect = lambda key: {
            'SENDER_EMAIL': 'test@example.com',
            'SENDER_PASSWORD': 'password123'
        }.get(key)
        
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        notifications.send_email_reminder(
            to_email="user@example.com",
            todo_title="Important Meeting",
            due_date="2025-12-01 14:30:00"
        )
        
        call_args = mock_server.send_message.call_args[0][0]
        email_body = call_args.get_payload()[0].get_payload()
        
        assert "⚡ RAAS" in call_args['Subject']
        assert "Important Meeting" in email_body
        assert "Never miss what matters" in email_body

class TestSMSNotifications:
    @patch('twilio.rest.Client')
    @patch('os.getenv')
    def test_send_sms_success(self, mock_getenv, mock_twilio):
        """Test successful SMS sending."""
        mock_getenv.side_effect = lambda key: {
            'TWILIO_ACCOUNT_SID': 'test_sid',
            'TWILIO_AUTH_TOKEN': 'test_token',
            'TWILIO_PHONE_NUMBER': '+1234567890'
        }.get(key)
        
        mock_client = MagicMock()
        mock_twilio.return_value = mock_client
        mock_client.messages.create.return_value = Mock(sid='test_message_id')
        
        result = notifications.send_sms_reminder(
            to_phone="+9876543210",
            todo_title="Test Task",
            due_date="2025-12-01 10:00:00"
        )
        
        assert result is True
        mock_client.messages.create.assert_called_once()
    
    @patch('twilio.rest.Client')
    @patch('os.getenv')
    def test_send_sms_no_recipient(self, mock_getenv, mock_twilio):
        """Test SMS with no recipient returns False."""
        result = notifications.send_sms_reminder(
            to_phone="",
            todo_title="Test Task",
            due_date="2025-12-01 10:00:00"
        )
        
        assert result is False
        mock_twilio.assert_not_called()
    
    @patch('twilio.rest.Client')
    @patch('os.getenv')
    def test_send_sms_no_credentials(self, mock_getenv, mock_twilio):
        """Test SMS with no Twilio credentials returns False."""
        mock_getenv.return_value = None
        
        result = notifications.send_sms_reminder(
            to_phone="+9876543210",
            todo_title="Test Task",
            due_date="2025-12-01 10:00:00"
        )
        
        assert result is False
    
    @patch('twilio.rest.Client')
    @patch('os.getenv')
    def test_send_sms_twilio_error(self, mock_getenv, mock_twilio):
        """Test SMS sending handles Twilio errors gracefully."""
        mock_getenv.side_effect = lambda key: {
            'TWILIO_ACCOUNT_SID': 'test_sid',
            'TWILIO_AUTH_TOKEN': 'test_token',
            'TWILIO_PHONE_NUMBER': '+1234567890'
        }.get(key)
        
        mock_client = MagicMock()
        mock_twilio.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("Twilio Error")
        
        result = notifications.send_sms_reminder(
            to_phone="+9876543210",
            todo_title="Test Task",
            due_date="2025-12-01 10:00:00"
        )
        
        assert result is False
    
    @patch('twilio.rest.Client')
    @patch('os.getenv')
    def test_sms_content_formatting(self, mock_getenv, mock_twilio):
        """Test that SMS content is properly formatted with RAAS branding."""
        mock_getenv.side_effect = lambda key: {
            'TWILIO_ACCOUNT_SID': 'test_sid',
            'TWILIO_AUTH_TOKEN': 'test_token',
            'TWILIO_PHONE_NUMBER': '+1234567890'
        }.get(key)
        
        mock_client = MagicMock()
        mock_twilio.return_value = mock_client
        
        notifications.send_sms_reminder(
            to_phone="+9876543210",
            todo_title="Important Meeting",
            due_date="2025-12-01 14:30:00"
        )
        
        call_args = mock_client.messages.create.call_args
        message_body = call_args[1]['body']
        
        assert "⚡ RAAS" in message_body
        assert "Important Meeting" in message_body

class TestWhatsAppNotifications:
    @patch('twilio.rest.Client')
    @patch('os.getenv')
    def test_send_whatsapp_success(self, mock_getenv, mock_twilio):
        """Test successful WhatsApp sending."""
        mock_getenv.side_effect = lambda key: {
            'TWILIO_ACCOUNT_SID': 'test_sid',
            'TWILIO_AUTH_TOKEN': 'test_token',
            'TWILIO_PHONE_NUMBER': '+1234567890'
        }.get(key)
        
        mock_client = MagicMock()
        mock_twilio.return_value = mock_client
        mock_client.messages.create.return_value = Mock(sid='test_message_id')
        
        result = notifications.send_whatsapp_reminder(
            to_whatsapp="+9876543210",
            todo_title="Test Task",
            due_date="2025-12-01 10:00:00"
        )
        
        assert result is True
        mock_client.messages.create.assert_called_once()
        
        call_args = mock_client.messages.create.call_args[1]
        assert call_args['from_'].startswith('whatsapp:')
        assert call_args['to'].startswith('whatsapp:')
    
    @patch('twilio.rest.Client')
    @patch('os.getenv')
    def test_send_whatsapp_no_recipient(self, mock_getenv, mock_twilio):
        """Test WhatsApp with no recipient returns False."""
        result = notifications.send_whatsapp_reminder(
            to_whatsapp="",
            todo_title="Test Task",
            due_date="2025-12-01 10:00:00"
        )
        
        assert result is False
        mock_twilio.assert_not_called()

class TestSendAllReminders:
    @patch('notifications.send_whatsapp_reminder')
    @patch('notifications.send_sms_reminder')
    @patch('notifications.send_email_reminder')
    def test_send_all_reminders_all_channels(self, mock_email, mock_sms, mock_whatsapp):
        """Test sending reminders to all available channels."""
        mock_email.return_value = True
        mock_sms.return_value = True
        mock_whatsapp.return_value = True
        
        todo = {
            'title': 'Test Task',
            'due_date': '2025-12-01 10:00:00',
            'email': 'test@example.com',
            'phone': '+1234567890',
            'whatsapp_phone': '+1234567890'
        }
        
        notifications.send_all_reminders(todo)
        
        mock_email.assert_called_once()
        mock_sms.assert_called_once()
        mock_whatsapp.assert_called_once()
    
    @patch('notifications.send_whatsapp_reminder')
    @patch('notifications.send_sms_reminder')
    @patch('notifications.send_email_reminder')
    def test_send_all_reminders_partial_channels(self, mock_email, mock_sms, mock_whatsapp):
        """Test sending reminders only to available channels."""
        mock_email.return_value = True
        mock_sms.return_value = False
        mock_whatsapp.return_value = False
        
        todo = {
            'title': 'Test Task',
            'due_date': '2025-12-01 10:00:00',
            'email': 'test@example.com',
            'phone': '',
            'whatsapp_phone': ''
        }
        
        notifications.send_all_reminders(todo)
        
        mock_email.assert_called_once()
        assert mock_sms.call_count <= 1
        assert mock_whatsapp.call_count <= 1
