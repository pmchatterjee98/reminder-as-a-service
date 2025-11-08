"""
Replit Auth integration for RAAS.
Provides authentication utilities for both Streamlit and FastAPI applications.
"""

import os
from typing import Optional, Dict, Tuple
from datetime import datetime
from database_auth import (
    init_auth_db,
    create_user,
    get_user_by_id,
    create_session,
    get_session,
    cleanup_expired_sessions
)


class ReplitAuthContext:
    """
    Handles Replit Auth context from HTTP headers.
    
    Replit Auth provides these headers when a user is authenticated:
    - X-Replit-User-Id: Unique user identifier from Replit
    - X-Replit-User-Name: Username
    - X-Replit-User-Roles: User roles (if applicable)
    """
    
    def __init__(self, user_id: Optional[str] = None, 
                 user_name: Optional[str] = None,
                 user_roles: Optional[str] = None):
        self.replit_user_id = user_id
        self.user_name = user_name
        self.user_roles = user_roles
        self.is_authenticated = user_id is not None
    
    @classmethod
    def from_headers(cls, headers: Dict[str, str]) -> 'ReplitAuthContext':
        """
        Create auth context from HTTP headers.
        
        Args:
            headers: Dictionary of HTTP headers
        
        Returns:
            ReplitAuthContext instance
        """
        # Replit Auth headers (case-insensitive lookup)
        headers_lower = {k.lower(): v for k, v in headers.items()}
        
        user_id = headers_lower.get('x-replit-user-id')
        user_name = headers_lower.get('x-replit-user-name')
        user_roles = headers_lower.get('x-replit-user-roles')
        
        return cls(user_id=user_id, user_name=user_name, user_roles=user_roles)
    
    @classmethod
    def from_streamlit(cls) -> 'ReplitAuthContext':
        """
        Create auth context from Streamlit headers.
        
        Returns:
            ReplitAuthContext instance
        """
        try:
            import streamlit as st
            # Use st.context.headers if available (Streamlit >= 1.32.0)
            if hasattr(st, 'context') and hasattr(st.context, 'headers'):
                headers = st.context.headers or {}
            else:
                # Fallback for older Streamlit versions
                from streamlit.web.server.websocket_headers import _get_websocket_headers
                headers = _get_websocket_headers() or {}
            return cls.from_headers(headers)
        except Exception as e:
            print(f"Error getting Streamlit headers: {e}")
            return cls()
    
    def __repr__(self):
        return f"ReplitAuthContext(user_id={self.replit_user_id}, name={self.user_name}, authenticated={self.is_authenticated})"


class AuthManager:
    """
    Manages user authentication and session creation.
    Bridges Replit Auth with RAAS user database.
    """
    
    def __init__(self):
        # Ensure database is initialized
        init_auth_db()
        # Cleanup expired sessions on startup
        cleanup_expired_sessions()
    
    def get_or_create_user(self, auth_context: ReplitAuthContext,
                          email: Optional[str] = None) -> Optional[Dict]:
        """
        Get existing user or create new user from Replit Auth context.
        
        Args:
            auth_context: ReplitAuthContext with user info
            email: User's email (optional, will prompt if not provided)
        
        Returns:
            User dictionary if successful, None otherwise
        """
        if not auth_context.is_authenticated:
            return None
        
        # Try to find user by Replit auth provider ID
        from database_auth import DB_NAME
        import sqlite3
        
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM users 
            WHERE auth_provider = 'replit' 
            AND auth_provider_id = ? 
            AND is_active = 1
        ''', (auth_context.replit_user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            # User exists, return user info
            user = dict(row)
            from database_auth import encryption_manager
            decrypted = encryption_manager.decrypt_contact_info(
                email_encrypted=user.get('email_encrypted'),
                phone_encrypted=user.get('phone_encrypted'),
                whatsapp_encrypted=user.get('whatsapp_encrypted')
            )
            user['email_decrypted'] = decrypted['email']
            user['phone_decrypted'] = decrypted['phone']
            user['whatsapp_decrypted'] = decrypted['whatsapp']
            return user
        
        # User doesn't exist - need email to create
        if not email:
            return None
        
        # Create new user
        user_id = create_user(
            email=email,
            auth_provider='replit',
            auth_provider_id=auth_context.replit_user_id,
            consent_email=False,  # Will be set during onboarding
            consent_sms=False,
            consent_whatsapp=False
        )
        
        if user_id:
            return get_user_by_id(user_id)
        
        return None
    
    def create_or_refresh_session(self, user_id: str, 
                                  device_fingerprint: Optional[str] = None) -> Optional[str]:
        """
        Create a new session or refresh existing session for a user.
        
        Args:
            user_id: User's ID
            device_fingerprint: Optional device identifier
        
        Returns:
            Session ID if successful, None otherwise
        """
        return create_session(user_id=user_id, device_fingerprint=device_fingerprint)
    
    def get_user_from_session(self, session_id: str) -> Optional[Dict]:
        """
        Get user information from session ID.
        
        Args:
            session_id: Session identifier
        
        Returns:
            User dictionary if session is valid, None otherwise
        """
        session = get_session(session_id)
        if not session:
            return None
        
        return get_user_by_id(session['user_id'])


def get_replit_auth_script() -> str:
    """
    Get the Replit Auth JavaScript snippet for HTML pages.
    
    Returns:
        HTML script tag for Replit Auth
    """
    return '''
    <script authed="location.reload()" src="https://auth.util.repl.co/script.js"></script>
    '''


def get_login_html(message: str = "Please sign in with your Replit account") -> str:
    """
    Generate HTML for Replit Auth login page.
    
    Args:
        message: Message to display on login page
    
    Returns:
        HTML string with login UI
    """
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>RAAS - Sign In</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #0b0b0f 0%, #1a1520 100%);
                color: #F8F9FA;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }}
            .login-container {{
                background: rgba(255, 255, 255, 0.05);
                border-radius: 16px;
                padding: 48px;
                text-align: center;
                max-width: 400px;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
            .logo {{
                font-size: 48px;
                margin-bottom: 16px;
            }}
            h1 {{
                color: #6C5CE7;
                margin: 0 0 8px 0;
                font-size: 32px;
            }}
            .tagline {{
                color: #00D1B2;
                font-size: 14px;
                margin-bottom: 32px;
            }}
            p {{
                color: #F8F9FA;
                margin-bottom: 32px;
                line-height: 1.6;
            }}
            .auth-button {{
                margin: 0 auto;
            }}
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="logo">⚡</div>
            <h1>RAAS</h1>
            <div class="tagline">Reminder as a Service</div>
            <p>{message}</p>
            <div class="auth-button">
                {get_replit_auth_script()}
            </div>
        </div>
    </body>
    </html>
    '''


# Global auth manager instance
auth_manager = AuthManager()
