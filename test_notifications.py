import pytest
from unittest.mock import Mock, patch, MagicMock
import notifications
from datetime import datetime

class TestEmailNotifications:
    @patch('smtplib.SMTP')
    @patch('os.getenv')
    def test_send_email_success(self, mock_getenv, mock_smtp):
        """Test successful email sending."""
        mock_getenv.side_effect = lambda key, default=None: {
            'SENDER_EMAIL': 'test@example.com',
            'SENDER_PASSWORD': 'password123',
            'SMTP_SERVER': 'smtp.gmail.com',
            'SMTP_PORT': '587'
        }.get(key, default)
        
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
        # Return defaults for SMTP_SERVER and SMTP_PORT, but None for credentials
        mock_getenv.side_effect = lambda key, default=None: {
            'SMTP_SERVER': 'smtp.gmail.com',
            'SMTP_PORT': '587',
            'SENDER_EMAIL': None,
            'SENDER_PASSWORD': None
        }.get(key, default)
        
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
        mock_getenv.side_effect = lambda key, default=None: {
            'SENDER_EMAIL': 'test@example.com',
            'SENDER_PASSWORD': 'password123',
            'SMTP_SERVER': 'smtp.gmail.com',
            'SMTP_PORT': '587'
        }.get(key, default)
        
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
        mock_getenv.side_effect = lambda key, default=None: {
            'SENDER_EMAIL': 'test@example.com',
            'SENDER_PASSWORD': 'password123',
            'SMTP_SERVER': 'smtp.gmail.com',
            'SMTP_PORT': '587'
        }.get(key, default)
        
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        notifications.send_email_reminder(
            to_email="user@example.com",
            todo_title="Important Meeting",
            due_date="2025-12-01 14:30:00"
        )
        
        call_args = mock_server.send_message.call_args[0][0]
        
        # Check subject
        assert "⚡ RAAS" in call_args['Subject']
        
        # Get email body (decode if base64 encoded)
        import base64
        email_payload = call_args.get_payload()[0].get_payload()
        try:
            email_body = base64.b64decode(email_payload).decode('utf-8')
        except:
            email_body = email_payload
        
        assert "Important Meeting" in email_body
        assert "Never miss what matters" in email_body

class TestSMSNotifications:
    @patch('twilio.rest.Client')
    @patch('os.getenv')
    def test_send_sms_success(self, mock_getenv, mock_twilio):
        """Test successful SMS sending."""
        mock_getenv.side_effect = lambda key, default=None: {
            'TWILIO_ACCOUNT_SID': 'test_sid',
            'TWILIO_AUTH_TOKEN': 'test_token',
            'TWILIO_PHONE_NUMBER': '+1234567890'
        }.get(key, default)
        
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
        mock_getenv.side_effect = lambda key, default=None: {
            'TWILIO_ACCOUNT_SID': 'test_sid',
            'TWILIO_AUTH_TOKEN': 'test_token',
            'TWILIO_PHONE_NUMBER': '+1234567890'
        }.get(key, default)
        
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
        mock_getenv.side_effect = lambda key, default=None: {
            'TWILIO_ACCOUNT_SID': 'test_sid',
            'TWILIO_AUTH_TOKEN': 'test_token',
            'TWILIO_PHONE_NUMBER': '+1234567890'
        }.get(key, default)
        
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
        mock_getenv.side_effect = lambda key, default=None: {
            'TWILIO_ACCOUNT_SID': 'test_sid',
            'TWILIO_AUTH_TOKEN': 'test_token',
            'TWILIO_PHONE_NUMBER': '+1234567890'
        }.get(key, default)
        
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

