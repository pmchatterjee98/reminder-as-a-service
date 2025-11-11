"""
Authentication UI pages for RAAS
Handles login, signup, and magic link verification flows
"""

import streamlit as st
import os
from auth_email import (
    create_magic_link,
    send_magic_link_email,
    verify_magic_link,
    create_email_session,
    get_user_by_email
)
import database_auth


def show_login_page():
    """Display login/signup page with email magic link"""
    
    st.set_page_config(
        page_title="RAAS — Log In",
        page_icon="⚡",
        layout="centered"
    )
    
    # Header
    st.markdown("""
    <div style="text-align: center; margin-top: 3rem;">
        <h1 style="font-size: 48px; margin-bottom: 16px;">⚡</h1>
        <h1 style="color: #6C5CE7; margin: 0 0 8px 0; font-size: 32px;">RAAS</h1>
        <p style="color: #00D1B2; font-size: 14px; margin-bottom: 32px;">Reminder as a Service — Never miss what matters</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Check if we're processing a magic link token
    query_params = st.query_params
    if 'token' in query_params:
        handle_magic_link_verification(query_params['token'])
        return
    
    # Check if link was just sent
    if st.session_state.get('magic_link_sent', False):
        show_check_email_message()
        return
    
    # Show email input form
    show_email_input_form()


def show_email_input_form():
    """Display email input form for login/signup"""
    
    st.info("🔐 **Log in or sign up with your email** — We'll send you a magic link")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.form("email_login_form"):
        email = st.text_input(
            "Email Address",
            placeholder="your@email.com",
            help="Enter your email to receive a login link"
        )
        
        st.caption("💡 No password needed! We'll send you a secure link to log in.")
        
        submitted = st.form_submit_button("📧 Send Magic Link", type="primary", use_container_width=True)
        
        if submitted:
            if not email or not email.strip():
                st.error("❌ Please enter your email address")
            elif '@' not in email or '.' not in email.split('@')[1]:
                st.error("❌ Please enter a valid email address")
            else:
                handle_magic_link_request(email.strip().lower())


def handle_magic_link_request(email: str):
    """Handle magic link creation and email sending"""
    
    with st.spinner("✨ Creating your magic link..."):
        # Create magic link token
        token = create_magic_link(email)
        
        if not token:
            st.error("❌ Failed to create login link. Please try again.")
            return
        
        # Get base URL for magic link
        base_url = get_base_url()
        
        # Send magic link email
        email_sent = send_magic_link_email(email, token, base_url)
        
        if email_sent:
            st.session_state.magic_link_sent = True
            st.session_state.magic_link_email = email
            st.rerun()
        else:
            st.error("❌ Failed to send email. Please check your email address and try again.")
            st.caption("💡 Make sure email credentials are configured in environment variables")


def show_check_email_message():
    """Display check email message after magic link is sent"""
    
    email = st.session_state.get('magic_link_email', '')
    
    st.success("✅ **Magic link sent!**")
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(108, 92, 231, 0.1) 0%, rgba(0, 209, 178, 0.1) 100%); 
                border-radius: 12px; padding: 2rem; margin: 2rem 0; border: 1px solid rgba(108, 92, 231, 0.3);">
        <h3 style="color: #00D1B2; margin-top: 0; text-align: center;">📧 Check Your Email</h3>
        <p style="color: rgba(248, 249, 250, 0.9); text-align: center; font-size: 1.1rem;">
            We sent a magic link to:<br>
            <strong style="color: #6C5CE7;">{email}</strong>
        </p>
        <p style="color: rgba(248, 249, 250, 0.7); text-align: center; margin-bottom: 0;">
            Click the link in your email to log in.<br>
            The link expires in 15 minutes.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📧 Resend Link", use_container_width=True):
            st.session_state.magic_link_sent = False
            st.rerun()
    
    with col2:
        if st.button("✏️ Change Email", use_container_width=True):
            st.session_state.magic_link_sent = False
            st.session_state.magic_link_email = None
            st.rerun()
    
    st.caption("💡 **Didn't receive the email?** Check your spam folder or try resending.")


def handle_magic_link_verification(token: str):
    """Verify magic link token and log user in"""
    
    with st.spinner("🔐 Verifying your login link..."):
        # Verify the token
        email = verify_magic_link(token)
        
        if not email:
            st.error("❌ **Invalid or expired login link**")
            st.markdown("""
            This link may have:
            - Already been used
            - Expired (links are valid for 15 minutes)
            - Been copied incorrectly
            """)
            
            if st.button("🔄 Request New Link", type="primary", use_container_width=True):
                # Clear query params and show login form
                st.query_params.clear()
                st.session_state.magic_link_sent = False
                st.rerun()
            
            st.stop()
        
        # Check if user exists
        user = get_user_by_email(email)
        
        if user:
            # Existing user - log them in
            login_user(user)
        else:
            # New user - show onboarding
            st.session_state.onboarding_email = email
            st.session_state.show_onboarding = True
            st.query_params.clear()
            st.rerun()


def login_user(user: dict):
    """Log in an existing user"""
    
    # Create session
    device_info = f"Streamlit Web App"
    session_id = create_email_session(user['id'], user.get('email', ''), device_info)
    
    if session_id:
        # Store session in Streamlit session state
        st.session_state.session_id = session_id
        st.session_state.user_id = user['id']
        st.session_state.user_data = user
        st.session_state.show_onboarding = False
        
        # Clear query params
        st.query_params.clear()
        
        # Show success and redirect
        st.success(f"✅ **Welcome back, {user.get('name', 'User')}!**")
        st.balloons()
        
        import time
        time.sleep(1)
        st.rerun()
    else:
        st.error("❌ Failed to create session. Please try again.")


def get_base_url() -> str:
    """Get the base URL for the application"""
    
    # Try to get from Replit domains
    replit_domains = os.getenv('REPLIT_DOMAINS', '')
    if replit_domains:
        domain = replit_domains.split(',')[0]
        return f"https://{domain}"
    
    # Try to get from Replit dev domain
    repl_slug = os.getenv('REPL_SLUG', '')
    repl_owner = os.getenv('REPL_OWNER', '')
    if repl_slug and repl_owner:
        return f"https://{repl_slug}.{repl_owner}.repl.co"
    
    # Fallback for local development
    return "http://localhost:5000"


def show_onboarding_page(email: str):
    """Show onboarding page for new users"""
    
    st.set_page_config(
        page_title="Welcome to RAAS",
        page_icon="⚡",
        layout="centered"
    )
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="color: #6C5CE7; margin-bottom: 0.5rem;">⚡ Welcome to RAAS</h1>
        <p style="color: rgba(248, 249, 250, 0.7); font-size: 1.1rem;">
            Reminder as a Service — Never miss what matters
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.info(f"👋 Let's set up your account for **{email}**")
    
    with st.form("onboarding_form"):
        st.subheader("👤 Profile Information")
        st.write("Tell us about yourself.")
        
        name = st.text_input("Full Name *", placeholder="John Doe")
        username = st.text_input("Username *", placeholder="Choose a unique username")
        
        st.subheader("📱 Additional Contact Methods")
        st.write("Add optional contact methods for SMS and WhatsApp reminders.")
        
        phone = st.text_input("Phone (for SMS)", placeholder="+1234567890")
        whatsapp = st.text_input("WhatsApp", placeholder="+1234567890")
        
        st.subheader("🔔 Notification Preferences")
        st.write("Choose how you'd like to receive reminders:")
        
        consent_email = st.checkbox("Send me email reminders", value=True)
        consent_sms = st.checkbox("Send me SMS reminders", value=False)
        consent_whatsapp = st.checkbox("Send me WhatsApp reminders", value=False)
        
        st.caption("💡 You can change these preferences anytime in your profile.")
        
        submitted = st.form_submit_button("🚀 Complete Setup & Start Using RAAS", use_container_width=True, type="primary")
        
        if submitted:
            # Validation
            errors = []
            
            if not name or not name.strip():
                errors.append("Full Name is required")
            if not username or not username.strip():
                errors.append("Username is required")
            
            # Check at least one notification method is enabled
            if not consent_email and not consent_sms and not consent_whatsapp:
                errors.append("Please enable at least one notification method to receive reminders")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                # Create user
                user_id = database_auth.create_user(
                    email=email,
                    auth_provider='email',
                    auth_provider_id=email,  # Use email as provider ID for email auth
                    username=username.strip(),
                    name=name.strip(),
                    phone=phone.strip() if phone else None,
                    whatsapp=whatsapp.strip() if whatsapp else None,
                    consent_email=consent_email,
                    consent_sms=consent_sms,
                    consent_whatsapp=consent_whatsapp
                )
                
                if user_id and user_id not in ['DUPLICATE_USERNAME', 'DUPLICATE_EMAIL']:
                    # Get full user data
                    user = database_auth.get_user_by_id(user_id)
                    
                    # Log the user in
                    login_user(user)
                    
                elif user_id == 'DUPLICATE_USERNAME':
                    st.error(f"❌ Username **{username.strip()}** is already taken. Please choose a different username.")
                elif user_id == 'DUPLICATE_EMAIL':
                    st.error(f"❌ This email is already registered. Please use the login link sent to your email.")
                else:
                    st.error("❌ Failed to create account due to a database error. Please try again or contact support.")
