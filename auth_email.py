"""
Email Magic Link Authentication for RAAS
Standalone authentication system that works on any hosting platform
"""

import os
import sqlite3
import secrets
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, Dict
from security import EncryptionManager, hash_email

# Initialize encryption manager
encryption_manager = EncryptionManager()

DB_NAME = 'todos.db'

def init_email_auth_db():
    """Initialize email auth tables"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Create magic_links table for passwordless authentication
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS magic_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            token TEXT NOT NULL UNIQUE,
            expires_at TIMESTAMP NOT NULL,
            used BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create email_sessions table for user sessions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            email TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            device_info TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Create indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_magic_links_token ON magic_links(token)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_magic_links_email ON magic_links(email)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_email_sessions_user ON email_sessions(user_id)')
    
    conn.commit()
    conn.close()
    print("Email auth database initialized")


def generate_magic_link_token() -> str:
    """Generate a secure random token for magic links"""
    return secrets.token_urlsafe(32)


def create_magic_link(email: str, expires_minutes: int = 15) -> Optional[str]:
    """
    Create a magic link token for email authentication
    
    Args:
        email: User's email address
        expires_minutes: Token expiration time in minutes
    
    Returns:
        Token string if successful, None otherwise
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Clean up expired tokens for this email
        cursor.execute('DELETE FROM magic_links WHERE email = ? AND expires_at < ?', 
                      (email, datetime.now()))
        
        # Generate new token
        token = generate_magic_link_token()
        expires_at = datetime.now() + timedelta(minutes=expires_minutes)
        
        cursor.execute('''
            INSERT INTO magic_links (email, token, expires_at)
            VALUES (?, ?, ?)
        ''', (email, token, expires_at))
        
        conn.commit()
        conn.close()
        
        print(f"Magic link created for {email}, expires at {expires_at}")
        return token
        
    except Exception as e:
        print(f"Error creating magic link: {e}")
        return None


def verify_magic_link(token: str) -> Optional[str]:
    """
    Verify a magic link token and return the associated email
    
    Args:
        token: Magic link token
    
    Returns:
        Email address if valid, None otherwise
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT email, expires_at, used 
            FROM magic_links 
            WHERE token = ?
        ''', (token,))
        
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return None
        
        email, expires_at, used = result
        expires_at = datetime.fromisoformat(expires_at)
        
        # Check if token is expired or already used
        if datetime.now() > expires_at:
            conn.close()
            print(f"Magic link expired for {email}")
            return None
        
        if used:
            conn.close()
            print(f"Magic link already used for {email}")
            return None
        
        # Mark token as used
        cursor.execute('UPDATE magic_links SET used = 1 WHERE token = ?', (token,))
        conn.commit()
        conn.close()
        
        print(f"Magic link verified for {email}")
        return email
        
    except Exception as e:
        print(f"Error verifying magic link: {e}")
        return None


def send_magic_link_email(email: str, token: str, base_url: str) -> bool:
    """
    Send magic link email to user
    
    Args:
        email: Recipient email address
        token: Magic link token
        base_url: Base URL of the application
    
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Get SMTP credentials from environment
        sender_email = os.getenv('SENDER_EMAIL')
        sender_password = os.getenv('SENDER_PASSWORD')
        
        if not sender_email or not sender_password:
            print("SMTP credentials not configured")
            return False
        
        # Construct magic link URL
        magic_link = f"{base_url}?token={token}"
        
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = '🔐 Your RAAS Login Link'
        msg['From'] = f"RAAS <{sender_email}>"
        msg['To'] = email
        
        # Email body (text version)
        text = f"""
Hello!

Click the link below to log in to your RAAS account:

{magic_link}

This link will expire in 15 minutes and can only be used once.

If you didn't request this login link, you can safely ignore this email.

⚡ RAAS — Reminder as a Service
Never miss what matters
        """
        
        # Email body (HTML version)
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .container {{
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 12px;
            padding: 40px;
            text-align: center;
        }}
        .logo {{
            font-size: 48px;
            margin-bottom: 16px;
        }}
        h1 {{
            color: #6C5CE7;
            margin: 0 0 8px 0;
        }}
        .tagline {{
            color: #00D1B2;
            font-size: 14px;
            margin-bottom: 24px;
        }}
        .button {{
            display: inline-block;
            background: linear-gradient(135deg, #6C5CE7 0%, #5f4dd3 100%);
            color: white;
            text-decoration: none;
            padding: 16px 32px;
            border-radius: 8px;
            font-weight: bold;
            margin: 24px 0;
        }}
        .button:hover {{
            background: linear-gradient(135deg, #5f4dd3 0%, #5241bc 100%);
        }}
        .footer {{
            color: #6c757d;
            font-size: 12px;
            margin-top: 24px;
        }}
        .warning {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 12px;
            margin: 16px 0;
            text-align: left;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">⚡</div>
        <h1>RAAS</h1>
        <p class="tagline">Reminder as a Service</p>
        
        <p style="font-size: 18px; margin: 24px 0;">
            Click the button below to log in to your account
        </p>
        
        <a href="{magic_link}" class="button">
            🔐 Log In to RAAS
        </a>
        
        <div class="warning">
            <strong>⏰ Important:</strong> This link expires in 15 minutes and can only be used once.
        </div>
        
        <p class="footer">
            If you didn't request this login link, you can safely ignore this email.<br>
            Never share this link with anyone.
        </p>
    </div>
</body>
</html>
        """
        
        # Attach parts
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        print(f"Magic link email sent to {email}")
        return True
        
    except Exception as e:
        print(f"Error sending magic link email: {e}")
        return False


def create_email_session(user_id: str, email: str, device_info: str = None, 
                         session_duration_days: int = 30) -> Optional[str]:
    """
    Create a new email-based session for a user
    
    Args:
        user_id: User's ID
        email: User's email
        device_info: Optional device information
        session_duration_days: Session duration in days
    
    Returns:
        Session ID if successful, None otherwise
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(days=session_duration_days)
        
        cursor.execute('''
            INSERT INTO email_sessions (id, user_id, email, expires_at, device_info)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, user_id, email, expires_at, device_info))
        
        conn.commit()
        conn.close()
        
        print(f"Email session created for user {user_id}")
        return session_id
        
    except Exception as e:
        print(f"Error creating email session: {e}")
        return None


def get_email_session(session_id: str) -> Optional[Dict]:
    """
    Get session information by session ID
    
    Args:
        session_id: Session identifier
    
    Returns:
        Session dictionary if valid, None otherwise
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM email_sessions 
            WHERE id = ? AND expires_at > ?
        ''', (session_id, datetime.now()))
        
        row = cursor.fetchone()
        
        if row:
            # Update last accessed time
            cursor.execute('''
                UPDATE email_sessions 
                SET last_accessed = ? 
                WHERE id = ?
            ''', (datetime.now(), session_id))
            conn.commit()
            
            result = dict(row)
            conn.close()
            return result
        
        conn.close()
        return None
        
    except Exception as e:
        print(f"Error getting email session: {e}")
        return None


def delete_email_session(session_id: str) -> bool:
    """
    Delete a session (logout)
    
    Args:
        session_id: Session identifier
    
    Returns:
        True if deleted, False otherwise
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM email_sessions WHERE id = ?', (session_id,))
        
        conn.commit()
        conn.close()
        
        print(f"Email session deleted: {session_id}")
        return True
        
    except Exception as e:
        print(f"Error deleting email session: {e}")
        return False


def cleanup_expired_sessions():
    """Clean up expired sessions and magic links"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Delete expired sessions
        cursor.execute('DELETE FROM email_sessions WHERE expires_at < ?', (datetime.now(),))
        sessions_deleted = cursor.rowcount
        
        # Delete expired magic links
        cursor.execute('DELETE FROM magic_links WHERE expires_at < ?', (datetime.now(),))
        links_deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        if sessions_deleted > 0 or links_deleted > 0:
            print(f"Cleaned up {sessions_deleted} expired sessions and {links_deleted} expired magic links")
        
        return True
        
    except Exception as e:
        print(f"Error cleaning up expired data: {e}")
        return False


def get_user_by_email(email: str) -> Optional[Dict]:
    """
    Get user by email address
    
    Args:
        email: User's email
    
    Returns:
        User dictionary if found, None otherwise
    """
    try:
        import database_auth
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Hash the email for lookup
        email_hash = hash_email(email)
        
        cursor.execute('''
            SELECT * FROM users 
            WHERE email_hash = ? AND is_active = 1
        ''', (email_hash,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
        
    except Exception as e:
        print(f"Error getting user by email: {e}")
        return None
