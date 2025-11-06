import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

def send_email_reminder(to_email: str, todo_title: str, due_date: str) -> bool:
    """Send an email reminder for a todo item."""
    if not to_email or to_email.strip() == "":
        return False
    
    # Email configuration from environment variables
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    
    if not sender_email or not sender_password:
        print("Email credentials not configured. Set SENDER_EMAIL and SENDER_PASSWORD.")
        return False
    
    try:
        # Create message
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = to_email
        message["Subject"] = f"Reminder: {todo_title}"
        
        body = f"""
        This is a reminder for your todo item:
        
        Title: {todo_title}
        Due Date: {due_date}
        
        Don't forget to complete this task!
        """
        
        message.attach(MIMEText(body, "plain"))
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)
        
        print(f"Email sent successfully to {to_email}")
        return True
    
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

def send_sms_reminder(to_phone: str, todo_title: str, due_date: str) -> bool:
    """Send an SMS reminder for a todo item using Twilio."""
    if not to_phone or to_phone.strip() == "":
        return False
    
    try:
        from twilio.rest import Client
    except ImportError:
        print("Twilio not installed. Install with: pip install twilio")
        return False
    
    # Twilio configuration from environment variables
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_phone = os.getenv("TWILIO_PHONE_NUMBER")
    
    if not all([account_sid, auth_token, from_phone]):
        print("Twilio credentials not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER.")
        return False
    
    try:
        client = Client(account_sid, auth_token)
        
        message_body = f"Reminder: {todo_title}\nDue: {due_date}\n\nDon't forget to complete this task!"
        
        message = client.messages.create(
            body=message_body,
            from_=from_phone,
            to=to_phone
        )
        
        print(f"SMS sent successfully to {to_phone}. SID: {message.sid}")
        return True
    
    except Exception as e:
        print(f"Failed to send SMS: {str(e)}")
        return False
