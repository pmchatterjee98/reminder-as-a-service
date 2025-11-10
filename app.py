import streamlit as st
from datetime import datetime, timedelta
import database
import database_multi_user
import database_auth
import scheduler
import csv
import io
from auth_replit import ReplitAuthContext, auth_manager, get_login_html

# Initialize databases
database.init_db()
database_auth.init_auth_db()

# Start the reminder scheduler
scheduler.start_scheduler()

#=============================================================================
# AUTHENTICATION LAYER
#=============================================================================

# Get Replit Auth context
auth_context = ReplitAuthContext.from_streamlit()

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'show_onboarding' not in st.session_state:
    st.session_state.show_onboarding = False
if 'logged_out' not in st.session_state:
    st.session_state.logged_out = False
if 'logout_username' not in st.session_state:
    st.session_state.logout_username = None

# Check if user intentionally logged out
if st.session_state.logged_out:
    # Show login screen
    st.set_page_config(
        page_title="RAAS — Logged Out",
        page_icon="⚡",
        layout="centered"
    )
    
    # Show logout confirmation
    st.markdown("""
    <div style="text-align: center; margin-top: 3rem;">
        <h1 style="font-size: 48px; margin-bottom: 16px;">⚡</h1>
        <h1 style="color: #6C5CE7; margin: 0 0 8px 0; font-size: 32px;">RAAS</h1>
        <p style="color: #00D1B2; font-size: 14px; margin-bottom: 32px;">Reminder as a Service</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.logout_username:
        st.success(f"✅ You've been logged out successfully, **{st.session_state.logout_username}**")
    else:
        st.success("✅ You've been logged out successfully")
    
    st.markdown("""
    <div style="background: rgba(108, 92, 231, 0.1); border-left: 4px solid #6C5CE7; padding: 1rem; border-radius: 8px; margin: 1.5rem 0;">
        <h4 style="color: #6C5CE7; margin-top: 0;">Choose Your Next Step</h4>
        <p style="color: rgba(248, 249, 250, 0.9); line-height: 1.6; margin-bottom: 0.75rem;">
            <strong>Same Account:</strong> Click "Return to RAAS" to log back in as <strong>{}</strong>
        </p>
        <p style="color: rgba(248, 249, 250, 0.9); line-height: 1.6; margin-bottom: 0;">
            <strong>Different Account:</strong> Click "Sign in with Different Account" to log out of Replit and sign in with another username
        </p>
    </div>
    """.format(st.session_state.logout_username or "current user"), unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔐 Return to RAAS", type="primary", use_container_width=True):
            # Clear the logged_out flag to trigger normal auth flow
            st.session_state.logged_out = False
            st.session_state.logout_username = None
            st.rerun()
    
    with col2:
        # Use st.link_button for proper navigation in same window
        st.link_button("👤 Sign in with Different Account", "https://replit.com/logout", use_container_width=True)
    
    st.stop()

# Check if user is authenticated via Replit
if not auth_context.is_authenticated:
    # Show login page
    st.set_page_config(
        page_title="RAAS — Sign In",
        page_icon="⚡",
        layout="centered"
    )
    st.components.v1.html(get_login_html("Sign in with your Replit account to access RAAS"), height=600, scrolling=False)
    st.stop()

# User is authenticated - check if they exist in our database
if st.session_state.user_id is None:
    # Try to get or create user
    user = auth_manager.get_or_create_user(auth_context)
    
    if user is None:
        # New user needs onboarding
        st.session_state.show_onboarding = True
    else:
        # Existing user
        st.session_state.user_id = user['id']
        st.session_state.user_data = user
        
        # Delete completed tasks for this user on app refresh
        deleted_count = database_multi_user.delete_completed_tasks_for_user(user['id'])
        if deleted_count > 0:
            print(f"Removed {deleted_count} completed task(s) for user {user['id']} on refresh")

# Show onboarding if needed
if st.session_state.show_onboarding:
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
    
    st.info(f"👋 Hello, **{auth_context.user_name}**! Let's set up your account.")
    
    with st.form("onboarding_form"):
        st.subheader("👤 Profile Information")
        st.write("Tell us about yourself.")
        
        name = st.text_input("Full Name *", placeholder="John Doe", value=auth_context.user_name or "")
        username = st.text_input("Username *", placeholder="Choose a unique username")
        
        st.subheader("📧 Contact Information")
        st.write("We'll use this information to send you reminders.")
        
        email = st.text_input("Email Address *", placeholder="your@email.com")
        phone = st.text_input("Phone (for SMS)", placeholder="+1234567890")
        whatsapp = st.text_input("WhatsApp", placeholder="+1234567890")
        
        st.subheader("🔔 Notification Preferences")
        st.write("Choose how you'd like to receive reminders:")
        
        consent_email = st.checkbox("Send me email reminders", value=True)
        consent_sms = st.checkbox("Send me SMS reminders", value=False)
        consent_whatsapp = st.checkbox("Send me WhatsApp reminders", value=False)
        
        st.caption("You can change these preferences anytime in your profile.")
        
        submitted = st.form_submit_button("Complete Setup", use_container_width=True)
        
        if submitted:
            if email and name and username:
                # Create user with profile, contact info and consents
                user_id = database_auth.create_user(
                    email=email,
                    auth_provider='replit',
                    auth_provider_id=auth_context.replit_user_id,
                    username=username,
                    name=name,
                    phone=phone if phone else None,
                    whatsapp=whatsapp if whatsapp else None,
                    consent_email=consent_email,
                    consent_sms=consent_sms,
                    consent_whatsapp=consent_whatsapp
                )
                
                if user_id:
                    st.session_state.user_id = user_id
                    st.session_state.user_data = database_auth.get_user_by_id(user_id)
                    st.session_state.show_onboarding = False
                    st.success("✅ Account created successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to create account. Username may already be taken or there was an error.")
            else:
                st.error("⚠️ Please provide your name, username, and email address.")
    
    st.stop()

# User is fully authenticated and onboarded
current_user_id = st.session_state.user_id

# Always refresh user data from database to ensure we have the latest profile info
# This ensures that changes to name, username, etc. are immediately reflected
import database_auth
st.session_state.user_data = database_auth.get_user_by_id(current_user_id)
current_user = st.session_state.user_data

# Page configuration
st.set_page_config(
    page_title="RAAS — Reminder as a Service",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# PWA Meta Tags for iPhone installability
st.markdown("""
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="RAAS">
<meta name="mobile-web-app-capable" content="yes">
<meta name="theme-color" content="#6C5CE7">
<link rel="apple-touch-icon" href="https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/26a1.png">
<link rel="manifest" href="/manifest.json">
""", unsafe_allow_html=True)

# Custom CSS for RAAS branding and modern UI
st.markdown("""
<style>
    /* RAAS Color Palette */
    :root {
        --raap-primary: #6C5CE7;
        --raap-accent: #00D1B2;
        --raap-surface: #0b0b0f;
        --raap-card: #1a1a1f;
        --raap-text: #f8f9fa;
        --raap-high: #ff6b6b;
        --raap-medium: #ffd93d;
        --raap-low: #6bcf7f;
    }
    
    /* Main app styling */
    .stApp {
        background: linear-gradient(135deg, #0b0b0f 0%, #1a1520 100%);
    }
    
    /* Headers */
    h1 {
        color: var(--raap-primary) !important;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }
    
    h2 {
        color: var(--raap-accent) !important;
        font-size: 1.5rem !important;
        font-weight: 600 !important;
    }
    
    h3 {
        color: var(--raap-text) !important;
        font-size: 1.2rem !important;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a1f 0%, #0b0b0f 100%);
        border-right: 1px solid rgba(108, 92, 231, 0.2);
    }
    
    /* Form inputs */
    .stTextInput input, .stTextArea textarea, .stDateInput input, .stTimeInput input {
        background-color: rgba(26, 26, 31, 0.8) !important;
        border: 1px solid rgba(108, 92, 231, 0.3) !important;
        border-radius: 12px !important;
        color: var(--raap-text) !important;
        padding: 0.75rem !important;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--raap-primary) !important;
        box-shadow: 0 0 0 3px rgba(108, 92, 231, 0.2) !important;
    }
    
    /* Selectbox styling */
    .stSelectbox div[data-baseweb="select"] {
        background-color: rgba(26, 26, 31, 0.8) !important;
        border-radius: 12px !important;
    }
    
    /* Buttons */
    .stButton button {
        background: linear-gradient(135deg, var(--raap-primary) 0%, #5346c9 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(108, 92, 231, 0.3) !important;
    }
    
    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(108, 92, 231, 0.4) !important;
    }
    
    /* Download buttons */
    .stDownloadButton button {
        background: linear-gradient(135deg, var(--raap-accent) 0%, #00b89f 100%) !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
    }
    
    /* Cards and containers */
    .element-container {
        background: rgba(26, 26, 31, 0.6);
        border-radius: 16px;
        padding: 1rem;
    }
    
    /* Mobile Optimization */
    @media only screen and (max-width: 768px) {
        /* Adjust layout for mobile */
        .stApp {
            padding: 0.5rem !important;
        }
        
        /* Make headers smaller on mobile */
        h1 {
            font-size: 1.8rem !important;
        }
        
        h2 {
            font-size: 1.3rem !important;
        }
        
        /* Improve form spacing on mobile */
        .stTextInput input, .stTextArea textarea {
            font-size: 16px !important; /* Prevents zoom on iOS */
            padding: 0.6rem !important;
        }
        
        /* Better button sizing for touch */
        .stButton button {
            padding: 0.875rem 1rem !important;
            font-size: 0.95rem !important;
            min-height: 44px; /* iOS touch target */
        }
        
        /* Sidebar adjustments */
        [data-testid="stSidebar"] {
            width: 100% !important;
        }
        
        /* Better table/todo list on mobile */
        .element-container {
            padding: 0.75rem !important;
        }
        
        /* Priority badges more readable on mobile */
        span[style*="padding: 0.25rem"] {
            font-size: 0.7rem !important;
            padding: 0.2rem 0.6rem !important;
        }
    }
    
    /* Smaller mobile devices (iPhone SE, etc) */
    @media only screen and (max-width: 375px) {
        h1 {
            font-size: 1.5rem !important;
        }
        
        .stButton button {
            font-size: 0.85rem !important;
            padding: 0.75rem 0.875rem !important;
        }
    }
    
    /* Status badges */
    .status-high {
        background: var(--raap-high);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .status-medium {
        background: var(--raap-medium);
        color: #0b0b0f;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .status-low {
        background: var(--raap-low);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    /* Info boxes */
    .stAlert {
        background: rgba(26, 26, 31, 0.8) !important;
        border-left: 4px solid var(--raap-accent) !important;
        border-radius: 12px !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(26, 26, 31, 0.8) !important;
        border-radius: 12px !important;
        color: var(--raap-text) !important;
    }
    
    /* Dividers */
    hr {
        border-color: rgba(108, 92, 231, 0.2) !important;
    }
    
    /* Caption text */
    .stCaption {
        color: rgba(248, 249, 250, 0.7) !important;
    }
</style>
""", unsafe_allow_html=True)

# Header with branding and profile dropdown
col_header1, col_header2, col_header3 = st.columns([1, 3, 1])

with col_header1:
    st.write("")  # Spacer

with col_header2:
    # Centered branding
    user_display_name = current_user.get('name') or current_user.get('username') or auth_context.user_name or "there"
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 1rem;">
        <h1 style="margin-bottom: 0.5rem;">⚡ RAAS</h1>
        <p style="color: rgba(248, 249, 250, 0.7); font-size: 1.1rem; margin-top: 0;">
            Reminder as a Service — Never miss what matters
        </p>
        <p style="color: #00D1B2; font-size: 1.2rem; margin-top: 1rem; font-weight: 500;">
            👋 Hello, {user_display_name}!
        </p>
    </div>
    """, unsafe_allow_html=True)

with col_header3:
    # Account menu in top right
    with st.popover("Account", use_container_width=True):
        # Initialize menu view state
        if 'menu_view' not in st.session_state:
            st.session_state.menu_view = 'main'
        
        # Main menu
        if st.session_state.menu_view == 'main':
            st.markdown("""
            <div style="padding: 0.5rem 0;">
                <h4 style="margin: 0 0 1rem 0; color: #00D1B2;">Menu</h4>
            </div>
            """, unsafe_allow_html=True)
            
            # Show success message if profile/settings was just saved
            if 'profile_save_message' in st.session_state:
                st.success(st.session_state.profile_save_message)
                st.balloons()
                st.info("✅ Changes saved! You can close this menu now")
                del st.session_state.profile_save_message
            
            # Show success message if settings was just saved
            if 'settings_save_message' in st.session_state:
                st.success(st.session_state.settings_save_message)
                st.balloons()
                st.info("✅ Changes saved! You can close this menu now")
                del st.session_state.settings_save_message
            
            # Profile button
            if st.button("👤 Profile", use_container_width=True):
                st.session_state.menu_view = 'profile'
                st.rerun()
            
            # Settings button
            if st.button("⚙️ Settings", use_container_width=True):
                st.session_state.menu_view = 'settings'
                st.rerun()
            
            st.divider()
            
            # Logout button
            if st.button("🚪 Logout", use_container_width=True, type="primary"):
                # Store username before clearing user data
                if st.session_state.user_data:
                    username = st.session_state.user_data.get('username') or st.session_state.user_data.get('name') or auth_context.user_name
                    st.session_state.logout_username = username
                
                # Clear ALL session state
                st.session_state.logged_out = True
                st.session_state.user_id = None
                st.session_state.user_data = None
                st.session_state.show_onboarding = False
                st.session_state.menu_view = 'main'
                
                # Clear other session keys to ensure clean logout
                for key in list(st.session_state.keys()):
                    if key not in ['logged_out', 'logout_username']:
                        del st.session_state[key]
                
                st.rerun()
        
        # Profile view - now fully editable
        elif st.session_state.menu_view == 'profile':
            # Back button
            if st.button("← Back", use_container_width=True):
                st.session_state.menu_view = 'main'
                st.rerun()
            
            st.markdown(f"""
            <div style="padding: 0.5rem 0;">
                <h4 style="margin: 0 0 1rem 0; color: #00D1B2;">Your Profile</h4>
                <p style="color: #a0a0a0; font-size: 0.9rem; margin: 0;">Edit your personal information and notification preferences</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Profile Information Section
            st.write("**Personal Information**")
            
            # Name
            profile_name = st.text_input(
                "Full Name",
                value=current_user.get('name') or '',
                key="profile_name",
                placeholder="Your full name"
            )
            
            # Username
            profile_username = st.text_input(
                "Username",
                value=current_user.get('username') or '',
                key="profile_username",
                placeholder="Your username (without @)"
            )
            
            # Email
            profile_email = st.text_input(
                "Email",
                value=current_user.get('email_decrypted') or '',
                key="profile_email",
                placeholder="your.email@example.com"
            )
            
            # Phone
            profile_phone = st.text_input(
                "Phone (SMS)",
                value=current_user.get('phone_decrypted') or '',
                key="profile_phone",
                placeholder="+1234567890"
            )
            
            # WhatsApp
            profile_whatsapp = st.text_input(
                "WhatsApp",
                value=current_user.get('whatsapp_decrypted') or '',
                key="profile_whatsapp",
                placeholder="+1234567890"
            )
            
            st.divider()
            
            # Notification Preferences Section
            st.write("**Notification Preferences**")
            st.caption("Enable or disable notification channels:")
            
            # Email toggle
            profile_email_enabled = st.checkbox(
                "✉️ Email Notifications",
                value=bool(current_user.get('consent_email')),
                key="profile_email_consent",
                help="Receive reminders via email"
            )
            
            # SMS toggle
            profile_sms_enabled = st.checkbox(
                "📱 SMS Notifications",
                value=bool(current_user.get('consent_sms')),
                key="profile_sms",
                help="Receive reminders via SMS text messages"
            )
            
            # WhatsApp toggle
            profile_whatsapp_enabled = st.checkbox(
                "💬 WhatsApp Notifications",
                value=bool(current_user.get('consent_whatsapp')),
                key="profile_whatsapp_consent",
                help="Receive reminders via WhatsApp"
            )
            
            st.divider()
            
            # Save changes button
            if st.button("💾 Save Changes", type="primary", use_container_width=True):
                try:
                    errors = []
                    updated_fields = []
                    
                    # Track which fields were changed
                    name_changed = profile_name != (current_user.get('name') or '')
                    username_changed = profile_username != (current_user.get('username') or '')
                    email_changed = profile_email != (current_user.get('email_decrypted') or '')
                    phone_changed = profile_phone != (current_user.get('phone_decrypted') or '')
                    whatsapp_changed = profile_whatsapp != (current_user.get('whatsapp_decrypted') or '')
                    email_consent_changed = profile_email_enabled != bool(current_user.get('consent_email'))
                    sms_consent_changed = profile_sms_enabled != bool(current_user.get('consent_sms'))
                    whatsapp_consent_changed = profile_whatsapp_enabled != bool(current_user.get('consent_whatsapp'))
                    
                    # Update profile (name and username)
                    if name_changed or username_changed:
                        success_profile = database_auth.update_user_profile(
                            user_id=current_user_id,
                            name=profile_name.strip() if name_changed and profile_name else None,
                            username=profile_username.strip() if username_changed and profile_username else None
                        )
                        if success_profile:
                            if name_changed:
                                updated_fields.append("Name")
                            if username_changed:
                                updated_fields.append("Username")
                        else:
                            errors.append("Failed to update profile (username may already be taken)")
                    
                    # Update contact info
                    if email_changed or phone_changed or whatsapp_changed:
                        success_contact = database_auth.update_user_contact_info(
                            user_id=current_user_id,
                            email=profile_email.strip() if email_changed and profile_email else None,
                            phone=profile_phone.strip() if phone_changed and profile_phone else None,
                            whatsapp=profile_whatsapp.strip() if whatsapp_changed and profile_whatsapp else None
                        )
                        if success_contact:
                            if email_changed:
                                updated_fields.append("Email")
                            if phone_changed:
                                updated_fields.append("Phone")
                            if whatsapp_changed:
                                updated_fields.append("WhatsApp")
                        else:
                            errors.append("Failed to update contact info (check email/phone format)")
                    
                    # Update notification preferences
                    if email_consent_changed or sms_consent_changed or whatsapp_consent_changed:
                        success_consent = database_auth.update_user_consent(
                            user_id=current_user_id,
                            consent_email=profile_email_enabled,
                            consent_sms=profile_sms_enabled,
                            consent_whatsapp=profile_whatsapp_enabled
                        )
                        if success_consent:
                            if email_consent_changed:
                                updated_fields.append("Email Notifications")
                            if sms_consent_changed:
                                updated_fields.append("SMS Notifications")
                            if whatsapp_consent_changed:
                                updated_fields.append("WhatsApp Notifications")
                        else:
                            errors.append("Failed to update notification preferences")
                    
                    if errors:
                        for error in errors:
                            st.error(f"❌ {error}")
                    elif updated_fields:
                        # Refresh user data immediately from database
                        fresh_user_data = database_auth.get_user_by_id(current_user_id)
                        if fresh_user_data:
                            st.session_state.user_data = fresh_user_data
                            print(f"Profile updated: {fresh_user_data.get('name')}, {fresh_user_data.get('username')}")
                        
                        # Store success message in session state to persist across rerun
                        fields_str = ", ".join(updated_fields)
                        st.session_state.profile_save_message = f"✅ Successfully updated: {fields_str}"
                        
                        # Return to main menu (Streamlit will auto-rerun, don't call st.rerun() manually)
                        st.session_state.menu_view = 'main'
                    else:
                        st.info("ℹ️ No changes detected")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    print(f"Profile update error: {e}")
        
        # Settings view
        elif st.session_state.menu_view == 'settings':
            # Back button
            if st.button("← Back", use_container_width=True):
                st.session_state.menu_view = 'main'
                st.rerun()
            
            st.markdown("""
            <div style="padding: 0.5rem 0;">
                <h4 style="margin: 0 0 1rem 0; color: #00D1B2;">Settings</h4>
            </div>
            """, unsafe_allow_html=True)
            
            # Profile Information Section
            st.write("**Profile Information**")
            
            # Name
            name_input = st.text_input(
                "Full Name",
                value=current_user.get('name') or '',
                key="settings_name",
                placeholder="Your full name"
            )
            
            # Username
            username_input = st.text_input(
                "Username",
                value=current_user.get('username') or '',
                key="settings_username",
                placeholder="Your username (without @)"
            )
            
            # Email
            email_input = st.text_input(
                "Email",
                value=current_user.get('email_decrypted') or '',
                key="settings_email_input",
                placeholder="your.email@example.com"
            )
            
            # Phone
            phone_input = st.text_input(
                "Phone (SMS)",
                value=current_user.get('phone_decrypted') or '',
                key="settings_phone",
                placeholder="+1234567890"
            )
            
            # WhatsApp
            whatsapp_input = st.text_input(
                "WhatsApp",
                value=current_user.get('whatsapp_decrypted') or '',
                key="settings_whatsapp_input",
                placeholder="+1234567890"
            )
            
            st.divider()
            
            # Notification Preferences Section
            st.write("**Notification Preferences**")
            st.caption("Enable or disable notification channels:")
            
            # Email toggle
            email_enabled = st.checkbox(
                "✉️ Email Notifications",
                value=bool(current_user.get('consent_email')),
                key="settings_email_consent",
                help="Receive reminders via email"
            )
            
            # SMS toggle
            sms_enabled = st.checkbox(
                "📱 SMS Notifications",
                value=bool(current_user.get('consent_sms')),
                key="settings_sms",
                help="Receive reminders via SMS text messages"
            )
            
            # WhatsApp toggle
            whatsapp_enabled = st.checkbox(
                "💬 WhatsApp Notifications",
                value=bool(current_user.get('consent_whatsapp')),
                key="settings_whatsapp_consent",
                help="Receive reminders via WhatsApp"
            )
            
            st.divider()
            
            # Mobile Browser Notifications Section
            st.write("**📱 Mobile Alarms**")
            st.caption("Get instant browser notifications on your phone for tasks due within 24 hours")
            
            notification_enable_html = """
            <script>
            function enableNotifications() {
                if (!('Notification' in window)) {
                    alert('Your browser does not support notifications');
                    return;
                }
                
                Notification.requestPermission().then(permission => {
                    if (permission === 'granted') {
                        // Show a test notification
                        new Notification('⚡ RAAS Notifications Enabled!', {
                            body: 'You will now receive mobile alarms for tasks due within 24 hours',
                            icon: './app/static/icon-192.png',
                            badge: './app/static/icon-72.png',
                            vibrate: [200, 100, 200]
                        });
                        
                        // Update UI
                        document.getElementById('notification-status').innerHTML = 
                            '<div style="padding: 0.5rem; background: rgba(107, 207, 127, 0.2); border-radius: 8px; color: #6bcf7f; font-size: 0.9rem;">✅ Mobile alarms enabled</div>';
                        
                        // CRITICAL: Schedule notifications immediately after permission grant
                        // Use a small delay to ensure the scheduling function is loaded
                        function trySchedule(attempts = 0) {
                            if (window.raasScheduleNotifications) {
                                window.raasScheduleNotifications();
                                console.log('RAAS: Notifications scheduled after permission grant');
                            } else if (attempts < 10) {
                                // Retry after 100ms, up to 10 times (1 second total)
                                setTimeout(() => trySchedule(attempts + 1), 100);
                            } else {
                                console.warn('RAAS: Scheduling function not found after permission grant');
                            }
                        }
                        trySchedule();
                    } else if (permission === 'denied') {
                        alert('Notifications blocked. Please enable them in your browser settings.');
                    }
                });
            }
            
            // Check current permission status
            window.addEventListener('DOMContentLoaded', () => {
                if ('Notification' in window) {
                    const status = document.getElementById('notification-status');
                    if (Notification.permission === 'granted') {
                        status.innerHTML = 
                            '<div style="padding: 0.5rem; background: rgba(107, 207, 127, 0.2); border-radius: 8px; color: #6bcf7f; font-size: 0.9rem;">✅ Mobile alarms enabled</div>';
                    } else if (Notification.permission === 'denied') {
                        status.innerHTML = 
                            '<div style="padding: 0.5rem; background: rgba(255, 107, 107, 0.2); border-radius: 8px; color: #ff6b6b; font-size: 0.9rem;">❌ Blocked - Enable in browser settings</div>';
                    } else {
                        status.innerHTML = 
                            '<div style="padding: 0.5rem; background: rgba(255, 217, 61, 0.2); border-radius: 8px; color: #ffd93d; font-size: 0.9rem;">⚠️ Not enabled - Click button below</div>';
                    }
                }
            });
            </script>
            
            <div id="notification-status" style="margin-bottom: 0.75rem;">
                <div style="padding: 0.5rem; background: rgba(255, 217, 61, 0.2); border-radius: 8px; color: #ffd93d; font-size: 0.9rem;">⚠️ Checking status...</div>
            </div>
            
            <button onclick="enableNotifications()" style="
                width: 100%;
                padding: 0.75rem;
                background: linear-gradient(135deg, #6C5CE7 0%, #5a4bd4 100%);
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
            " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(108, 92, 231, 0.4)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">
                🔔 Enable Mobile Alarms
            </button>
            
            <p style="color: rgba(248, 249, 250, 0.5); font-size: 0.8rem; margin-top: 0.5rem;">
                💡 When enabled, you'll get browser notifications on your phone for tasks due within 24 hours while the app is open in a tab.
            </p>
            """
            
            st.components.v1.html(notification_enable_html, height=200)
            
            st.divider()
            
            # Save button
            if st.button("💾 Save Settings", use_container_width=True, type="primary"):
                from database_auth import update_user_consent, update_user_contact_info, update_user_profile, get_user_by_id
                
                errors = []
                updated_fields = []
                
                # Track which fields were changed
                name_changed = name_input != (current_user.get('name') or '')
                username_changed = username_input != (current_user.get('username') or '')
                email_changed = email_input != (current_user.get('email_decrypted') or '')
                phone_changed = phone_input != (current_user.get('phone_decrypted') or '')
                whatsapp_changed = whatsapp_input != (current_user.get('whatsapp_decrypted') or '')
                email_consent_changed = email_enabled != bool(current_user.get('consent_email'))
                sms_consent_changed = sms_enabled != bool(current_user.get('consent_sms'))
                whatsapp_consent_changed = whatsapp_enabled != bool(current_user.get('consent_whatsapp'))
                
                # Update profile (name and username)
                if name_input or username_input:
                    if name_changed or username_changed:
                        profile_success = update_user_profile(
                            user_id=st.session_state.user_id,
                            name=name_input if name_changed else None,
                            username=username_input if username_changed else None
                        )
                        if profile_success:
                            if name_changed:
                                updated_fields.append("Name")
                            if username_changed:
                                updated_fields.append("Username")
                        else:
                            errors.append("Failed to update profile (username may already be taken)")
                
                # Update contact info (email, phone, whatsapp)
                if email_changed or phone_changed or whatsapp_changed:
                    contact_success = update_user_contact_info(
                        user_id=st.session_state.user_id,
                        email=email_input if email_changed else None,
                        phone=phone_input if phone_changed else None,
                        whatsapp=whatsapp_input if whatsapp_changed else None
                    )
                    if contact_success:
                        if email_changed:
                            updated_fields.append("Email")
                        if phone_changed:
                            updated_fields.append("Phone")
                        if whatsapp_changed:
                            updated_fields.append("WhatsApp")
                    else:
                        errors.append("Failed to update contact info (check email/phone format)")
                
                # Update consent preferences
                if email_consent_changed or sms_consent_changed or whatsapp_consent_changed:
                    consent_success = update_user_consent(
                        user_id=st.session_state.user_id,
                        consent_email=email_enabled,
                        consent_sms=sms_enabled,
                        consent_whatsapp=whatsapp_enabled
                    )
                    if consent_success:
                        if email_consent_changed:
                            updated_fields.append("Email Notifications")
                        if sms_consent_changed:
                            updated_fields.append("SMS Notifications")
                        if whatsapp_consent_changed:
                            updated_fields.append("WhatsApp Notifications")
                    else:
                        errors.append("Failed to update notification preferences")
                
                if errors:
                    for error in errors:
                        st.error(f"❌ {error}")
                elif updated_fields:
                    # Refresh user data to reflect changes
                    st.session_state.user_data = get_user_by_id(st.session_state.user_id)
                    
                    # Store success message in session state to persist across rerun
                    fields_str = ", ".join(updated_fields)
                    st.session_state.settings_save_message = f"✅ Successfully updated: {fields_str}"
                    
                    # Return to main menu (Streamlit will auto-rerun, don't call st.rerun() manually)
                    st.session_state.menu_view = 'main'
                else:
                    st.info("ℹ️ No changes detected")

# Sidebar for adding/editing todos
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h2 style="margin: 0;">⏰ Reminder Panel</h2>
        <p style="color: rgba(248, 249, 250, 0.6); font-size: 0.9rem; margin-top: 0.5rem;">
            Never forget what matters
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("add_todo_form", clear_on_submit=True):
        title = st.text_input("Title *", placeholder="e.g., Finish project report")
        description = st.text_area("Description", placeholder="Add details about this task...")
        due_date = st.date_input("Due Date *", min_value=datetime.now().date())
        
        # 12-hour time input with AM/PM
        st.write("**Due Time** *")
        time_col1, time_col2, time_col3 = st.columns([1.5, 1.5, 1.5])
        
        # Calculate current hour in 12-hour format (1-12)
        current_hour_24 = datetime.now().hour
        current_hour_12 = current_hour_24 % 12 or 12  # Convert 0 to 12, keep 1-12
        
        with time_col1:
            hour_12 = st.selectbox("Hour (1-12)", options=list(range(1, 13)), index=current_hour_12 - 1, key="add_hour")
        with time_col2:
            minute = st.selectbox("Minute (00-59)", options=[f"{m:02d}" for m in range(0, 60)], index=datetime.now().minute, key="add_minute")
        with time_col3:
            am_pm = st.selectbox("AM/PM", options=["AM", "PM"], index=0 if datetime.now().hour < 12 else 1, key="add_ampm")
        
        st.subheader("Reminder Settings")
        st.info("⚡ Auto-reminders sent for all tasks within 24 hours of due date!")
        
        # Show user's registered contact methods (read-only info)
        user = st.session_state.user_data
        contact_methods = []
        if user:
            if user.get('consent_email') and user.get('email_decrypted'):
                contact_methods.append(f"📧 {user['email_decrypted']}")
            if user.get('consent_sms') and user.get('phone_decrypted'):
                contact_methods.append(f"📱 SMS: {user['phone_decrypted']}")
            if user.get('consent_whatsapp') and user.get('whatsapp_decrypted'):
                contact_methods.append(f"💬 WhatsApp: {user['whatsapp_decrypted']}")
        
        if contact_methods:
            st.caption("Reminders will be sent to:")
            for method in contact_methods:
                st.caption(f"  {method}")
        else:
            st.caption("⚠️ No notification methods enabled. Update your profile to receive reminders.")
        
        st.subheader("Organization")
        col_cat, col_pri = st.columns(2)
        with col_cat:
            category = st.text_input("Category", placeholder="e.g., Work, Personal")
        with col_pri:
            priority = st.selectbox("Priority", ["High", "Medium", "Low"], index=1)
        
        st.subheader("Recurrence")
        is_recurring = st.checkbox("Make this a recurring task")
        
        recurrence_frequency = None
        recurrence_interval = None
        
        if is_recurring:
            col_freq, col_int = st.columns(2)
            with col_freq:
                recurrence_frequency = st.selectbox("Repeat every", ["days", "weeks", "months", "years"])
            with col_int:
                recurrence_interval = st.number_input("Interval", min_value=1, value=1, step=1)
        
        submitted = st.form_submit_button("Add Todo", use_container_width=True)
        
        if submitted:
            if title and due_date:
                # Convert 12-hour time to 24-hour format
                hour_24 = hour_12
                if am_pm == "PM" and hour_12 != 12:
                    hour_24 = hour_12 + 12
                elif am_pm == "AM" and hour_12 == 12:
                    hour_24 = 0
                
                due_time = datetime.strptime(f"{hour_24}:{minute}", "%H:%M").time()
                
                # Combine date and time
                due_datetime = datetime.combine(due_date, due_time)
                
                # Use contact info from user's profile
                user = st.session_state.user_data
                email = user.get('email_decrypted') if (user and user.get('consent_email')) else None
                phone = user.get('phone_decrypted') if (user and user.get('consent_sms')) else None
                whatsapp_phone = user.get('whatsapp_decrypted') if (user and user.get('consent_whatsapp')) else None
                
                database_multi_user.add_todo_for_user(
                    user_id=current_user_id,
                    title=title,
                    description=description,
                    due_date=due_datetime.isoformat(),
                    email=email or "",
                    phone=phone or "",
                    whatsapp_phone=whatsapp_phone or "",
                    reminder_hours=24,  # Auto-reminder set to 24 hours
                    is_recurring=is_recurring,
                    recurrence_frequency=recurrence_frequency,
                    recurrence_interval=recurrence_interval,
                    category=category if category else None,
                    priority=priority
                )
                st.success("✅ Reminder added successfully!")
                st.rerun()
            else:
                st.error("⚠️ Please fill in the required fields (Title and Due Date)")

def export_to_csv(todos):
    """Export todos to CSV format."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Title', 'Description', 'Due Date', 'Priority', 'Category', 'Status', 'Recurring', 'Email', 'Phone'])
    
    # Write todos
    for todo in todos:
        writer.writerow([
            todo['title'],
            todo.get('description', ''),
            todo['due_date'],
            todo.get('priority', 'Medium'),
            todo.get('category', ''),
            'Completed' if todo['completed'] else 'Pending',
            'Yes' if todo.get('is_recurring') else 'No',
            todo.get('email', ''),
            todo.get('phone', '')
        ])
    
    return output.getvalue()

def display_todo(todo):
    """Display a single todo item with actions or edit form."""
    # Check if this todo is being edited
    # Ensure both IDs are compared as strings for consistency
    if 'editing_todo' in st.session_state and str(st.session_state.editing_todo) == str(todo['id']):
        # Display inline edit form
        st.markdown(f"""
        <div style="background: rgba(108, 92, 231, 0.1); border: 2px solid rgba(108, 92, 231, 0.3); border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">
            <h4 style="color: #00D1B2; margin: 0 0 1rem 0;">✏️ Editing: {todo['title']}</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Handle both formats: 'T' separator and space separator
        due_date_str = todo['due_date'].replace(' ', 'T') if ' ' in todo['due_date'] else todo['due_date']
        due_datetime = datetime.fromisoformat(due_date_str)
        
        # Use unique key for form to ensure proper re-rendering with values
        with st.form(f"edit_todo_form_{todo['id']}"):
            edit_title = st.text_input("Title", value=todo['title'])
            edit_description = st.text_area("Description", value=todo['description'] or "")
            edit_due_date = st.date_input("Due Date", value=due_datetime.date())
            
            # 12-hour time input with AM/PM for editing
            st.write("**Due Time**")
            edit_time_col1, edit_time_col2, edit_time_col3 = st.columns([1.5, 1.5, 1.5])
            
            # Convert current time to 12-hour format
            current_hour_24 = due_datetime.hour
            current_hour_12 = current_hour_24 % 12 or 12  # Convert 0 to 12, keep 1-12
            current_am_pm = "AM" if current_hour_24 < 12 else "PM"
            current_minute = due_datetime.minute
            
            with edit_time_col1:
                edit_hour_12 = st.selectbox("Hour (1-12)", options=list(range(1, 13)), index=current_hour_12 - 1, key=f"edit_hour_{todo['id']}")
            with edit_time_col2:
                edit_minute = st.selectbox("Minute (00-59)", options=[f"{m:02d}" for m in range(0, 60)], index=current_minute, key=f"edit_minute_{todo['id']}")
            with edit_time_col3:
                edit_am_pm = st.selectbox("AM/PM", options=["AM", "PM"], index=0 if current_am_pm == "AM" else 1, key=f"edit_ampm_{todo['id']}")
            
            st.caption("⚡ Auto-reminders sent when task is within 24 hours of due date")
            
            # Show user's registered contact methods (read-only info)
            user = st.session_state.user_data
            contact_methods = []
            if user:
                if user.get('consent_email') and user.get('email_decrypted'):
                    contact_methods.append(f"📧 {user['email_decrypted']}")
                if user.get('consent_sms') and user.get('phone_decrypted'):
                    contact_methods.append(f"📱 SMS: {user['phone_decrypted']}")
                if user.get('consent_whatsapp') and user.get('whatsapp_decrypted'):
                    contact_methods.append(f"💬 WhatsApp: {user['whatsapp_decrypted']}")
            
            if contact_methods:
                st.caption("Reminders will be sent to:")
                for method in contact_methods:
                    st.caption(f"  {method}")
            else:
                st.caption("⚠️ No notification methods enabled. Update your profile to receive reminders.")
            
            col_cat, col_pri = st.columns(2)
            with col_cat:
                edit_category = st.text_input("Category", value=todo.get('category') or "")
            with col_pri:
                current_priority = todo.get('priority', 'Medium')
                edit_priority = st.selectbox("Priority", ["High", "Medium", "Low"], 
                                            index=["High", "Medium", "Low"].index(current_priority) if current_priority in ["High", "Medium", "Low"] else 1)
            
            edit_is_recurring = st.checkbox("Make this a recurring task", value=bool(todo.get('is_recurring')))
            
            # Set defaults for recurrence settings
            default_frequency = todo.get('recurrence_frequency') or 'days'
            default_interval = todo.get('recurrence_interval') or 1
            
            edit_recurrence_frequency = default_frequency
            edit_recurrence_interval = default_interval
            
            if edit_is_recurring:
                col_freq, col_int = st.columns(2)
                with col_freq:
                    edit_recurrence_frequency = st.selectbox("Repeat every", ["days", "weeks", "months", "years"],
                                                            index=["days", "weeks", "months", "years"].index(default_frequency) if default_frequency in ["days", "weeks", "months", "years"] else 0)
                with col_int:
                    edit_recurrence_interval = st.number_input("Interval", min_value=1, value=int(default_interval), step=1)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Save Changes", use_container_width=True):
                    # Convert 12-hour time to 24-hour format
                    edit_hour_24 = edit_hour_12
                    if edit_am_pm == "PM" and edit_hour_12 != 12:
                        edit_hour_24 = edit_hour_12 + 12
                    elif edit_am_pm == "AM" and edit_hour_12 == 12:
                        edit_hour_24 = 0
                    
                    edit_due_time = datetime.strptime(f"{edit_hour_24}:{edit_minute}", "%H:%M").time()
                    edit_due_datetime = datetime.combine(edit_due_date, edit_due_time)
                    
                    # Use contact info from user's profile
                    user = st.session_state.user_data
                    edit_email = user.get('email_decrypted') if (user and user.get('consent_email')) else None
                    edit_phone = user.get('phone_decrypted') if (user and user.get('consent_sms')) else None
                    edit_whatsapp_phone = user.get('whatsapp_decrypted') if (user and user.get('consent_whatsapp')) else None
                    
                    database_multi_user.update_todo_for_user(
                        user_id=current_user_id,
                        todo_id=todo['id'],
                        title=edit_title or "",
                        description=edit_description or "",
                        due_date=edit_due_datetime.isoformat(),
                        email=edit_email or "",
                        phone=edit_phone or "",
                        whatsapp_phone=edit_whatsapp_phone or "",
                        reminder_hours=24,  # Auto-reminder set to 24 hours
                        is_recurring=edit_is_recurring,
                        recurrence_frequency=edit_recurrence_frequency if edit_is_recurring else None,
                        recurrence_interval=edit_recurrence_interval if edit_is_recurring else None,
                        category=edit_category if edit_category else None,
                        priority=edit_priority
                    )
                    del st.session_state.editing_todo
                    st.success("✅ Reminder updated!")
                    st.rerun()
            
            with col2:
                if st.form_submit_button("❌ Cancel", use_container_width=True):
                    del st.session_state.editing_todo
                    st.rerun()
        
        st.divider()
        return
    
    # Handle both formats: 'T' separator and space separator
    due_date_str = todo['due_date'].replace(' ', 'T') if ' ' in todo['due_date'] else todo['due_date']
    due = datetime.fromisoformat(due_date_str)
    now = datetime.now()
    
    # Calculate days remaining
    time_diff = due - now
    days_remaining = time_diff.days
    hours_remaining = time_diff.seconds // 3600
    
    # Create days remaining text
    if todo['completed']:
        days_text = "✅ Completed"
        days_color = "#6bcf7f"
    elif days_remaining < 0:
        days_abs = abs(days_remaining)
        days_text = f"🚨 Overdue by {days_abs} day{'s' if days_abs != 1 else ''}"
        days_color = "#ff6b6b"
    elif days_remaining == 0:
        if hours_remaining > 0:
            days_text = f"⏰ Due today in {hours_remaining} hour{'s' if hours_remaining != 1 else ''}"
            days_color = "#ffd93d"
        else:
            days_text = "⏰ Due today"
            days_color = "#ffd93d"
    elif days_remaining == 1:
        days_text = "⏰ Due tomorrow"
        days_color = "#ffd93d"
    else:
        days_text = f"📅 {days_remaining} days left"
        days_color = "#00D1B2"
    
    # Priority badge with RAAS colors
    priority = todo.get('priority', 'Medium')
    priority_colors = {
        "High": {"bg": "#ff6b6b", "text": "white"},
        "Medium": {"bg": "#ffd93d", "text": "#0b0b0f"},
        "Low": {"bg": "#6bcf7f", "text": "white"}
    }
    color = priority_colors.get(priority, priority_colors["Medium"])
    
    with st.container():
        # Task information row
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Priority badge + Title
            priority_badge = f'<span style="background: {color["bg"]}; color: {color["text"]}; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.75rem; font-weight: 600; margin-right: 0.75rem;">{priority.upper()}</span>'
            
            if todo['completed']:
                title_html = f'{priority_badge}<span style="text-decoration: line-through; color: rgba(248, 249, 250, 0.5); font-size: 1.1rem;">{todo["title"]}</span>'
            else:
                title_html = f'{priority_badge}<span style="font-weight: 600; color: #f8f9fa; font-size: 1.1rem;">{todo["title"]}</span>'
            
            st.markdown(title_html, unsafe_allow_html=True)
            
            # Category and description in smaller text
            info_parts = []
            if todo.get('category'):
                info_parts.append(f"📂 {todo['category']}")
            if todo['description']:
                info_parts.append(todo['description'])
            if info_parts:
                st.caption(" • ".join(info_parts))
        
        with col2:
            # Days remaining as prominent text
            days_html = f'<div style="text-align: right; padding-top: 0.25rem;"><span style="color: {days_color}; font-weight: 600; font-size: 0.95rem;">{days_text}</span></div>'
            st.markdown(days_html, unsafe_allow_html=True)
            
            # Show due date and time in smaller text
            st.caption(f"Due: {due.strftime('%b %d, %Y at %I:%M %p')}")
        
        # Action buttons row - displayed horizontally below task
        # Use container to ensure proper isolation of button events
        with st.container():
            btn_col1, btn_col2, btn_col3, btn_col4 = st.columns([1.2, 1, 1, 2.8])
            
            with btn_col1:
                complete_clicked = st.button("✓ Complete" if not todo['completed'] else "↶ Undo", key=f"complete_{todo['id']}", use_container_width=True)
            
            with btn_col2:
                edit_clicked = st.button("✏️ Edit", key=f"edit_{todo['id']}", use_container_width=True)
            
            with btn_col3:
                delete_clicked = st.button("🗑️ Delete", key=f"delete_{todo['id']}", use_container_width=True)
            
            # Handle button clicks AFTER all buttons are rendered
            if complete_clicked:
                database_multi_user.toggle_complete_for_user(todo['id'], current_user_id)
                st.rerun()
            elif edit_clicked:
                # Store the ID we want to edit
                st.session_state.editing_todo = str(todo['id'])
                st.rerun()
            elif delete_clicked:
                database_multi_user.delete_todo_for_user(todo['id'], current_user_id)
                st.rerun()
        
        st.divider()

# Main content area
st.markdown("""
<div style="margin-bottom: 1.5rem;">
    <h2 style="margin: 0;">📋 Your Reminders</h2>
    <p style="color: rgba(248, 249, 250, 0.6); font-size: 0.95rem; margin-top: 0.5rem;">
        Manage and track all your scheduled reminders
    </p>
</div>
""", unsafe_allow_html=True)

# Get all todos for current user
todos = database_multi_user.get_todos_for_user(current_user_id)

# DEBUG: Clear stale editing state if the task being edited no longer exists
if 'editing_todo' in st.session_state:
    editing_id = str(st.session_state.editing_todo)
    task_ids = [str(t['id']) for t in todos]
    if editing_id not in task_ids:
        # Task being edited was deleted, clear the state
        del st.session_state.editing_todo

# Inject Mobile Notification System
import json
todos_json = json.dumps([{
    'id': str(todo['id']),
    'title': todo['title'],
    'description': todo.get('description', ''),
    'due_date': todo['due_date'],
    'priority': todo.get('priority', 'Medium'),
    'completed': todo['completed']
} for todo in todos])

notification_html = f"""
<script>
// RAAS Mobile Notifications System - Inline version
(function() {{
    const tasks = {todos_json};
    
    // Check if notifications are supported and granted
    if (!('Notification' in window)) {{
        console.log('This browser does not support notifications');
        return;
    }}
    
    // Schedule notifications for tasks due within 24 hours
    function scheduleNotifications(tasks) {{
        const now = new Date();
        const twentyFourHoursFromNow = new Date(now.getTime() + 24 * 60 * 60 * 1000);
        
        tasks.forEach(task => {{
            if (task.completed) return;
            
            const dueDate = new Date(task.due_date);
            
            // Check if task is due within 24 hours
            if (dueDate > now && dueDate <= twentyFourHoursFromNow) {{
                // Calculate when to show notification (1 hour before, or now if < 1 hour left)
                const oneHourBefore = new Date(dueDate.getTime() - 60 * 60 * 1000);
                const notificationTime = oneHourBefore > now ? oneHourBefore : now;
                const delay = notificationTime.getTime() - now.getTime();
                
                // Schedule the notification
                setTimeout(() => {{
                    showNotification(task);
                }}, Math.max(delay, 0));
                
                console.log(`Scheduled notification for task "${{task.title}}" in ${{Math.round(delay/1000/60)}} minutes`);
            }}
        }});
    }}
    
    // Show notification for a task
    function showNotification(task) {{
        const dueDate = new Date(task.due_date);
        const now = new Date();
        const hoursLeft = Math.round((dueDate - now) / (1000 * 60 * 60));
        const minutesLeft = Math.round((dueDate - now) / (1000 * 60));
        
        let timeText;
        if (hoursLeft >= 1) {{
            timeText = `Due in ${{hoursLeft}} hour${{hoursLeft > 1 ? 's' : ''}}`;
        }} else if (minutesLeft > 0) {{
            timeText = `Due in ${{minutesLeft}} minute${{minutesLeft > 1 ? 's' : ''}}`;
        }} else {{
            timeText = 'Due now!';
        }}
        
        const priorityEmoji = task.priority === 'High' ? '🔴' : task.priority === 'Medium' ? '🟡' : '🟢';
        
        new Notification(`⚡ ${{task.title}}`, {{
            body: `${{priorityEmoji}} ${{timeText}}\\n${{task.description || 'No description'}}`,
            icon: '/app/static/icon-192.png',
            badge: '/app/static/icon-72.png',
            vibrate: [200, 100, 200, 100, 200],
            tag: `raas-task-${{task.id}}`,
            requireInteraction: true,
            silent: false
        }});
    }}
    
    // Expose scheduling function globally so it can be called after permission grant
    window.raasScheduleNotifications = function() {{
        if (Notification.permission === 'granted') {{
            scheduleNotifications(tasks);
            console.log('RAAS Notifications: Scheduling enabled for', tasks.length, 'tasks');
        }} else {{
            console.log('RAAS Notifications: Permission not granted. Current status:', Notification.permission);
        }}
    }};
    
    // Schedule immediately if permission is already granted
    if (Notification.permission === 'granted') {{
        scheduleNotifications(tasks);
        console.log('RAAS Notifications: Scheduling enabled for', tasks.length, 'tasks');
    }} else {{
        console.log('RAAS Notifications: Permission not granted. Current status:', Notification.permission);
    }}
    
    // Re-check and schedule when page becomes visible (tab focus)
    document.addEventListener('visibilitychange', function() {{
        if (!document.hidden && Notification.permission === 'granted') {{
            console.log('RAAS Notifications: Page visible, re-checking tasks...');
            scheduleNotifications(tasks);
        }}
    }});
}})();
</script>
"""

st.components.v1.html(notification_html, height=0)

if not todos:
    st.markdown("""
    <div style="text-align: center; padding: 3rem 1rem; background: rgba(26, 26, 31, 0.6); border-radius: 16px; border: 2px dashed rgba(108, 92, 231, 0.3);">
        <h3 style="color: rgba(248, 249, 250, 0.8);">No reminders yet</h3>
        <p style="color: rgba(248, 249, 250, 0.5); margin-top: 1rem;">
            Get started by adding your first reminder using the form on the left ✨
        </p>
    </div>
    """, unsafe_allow_html=True)
else:
    # Filter options
    col1, col2, col3 = st.columns([2, 2, 3])
    with col1:
        show_completed = st.checkbox("Show completed", value=True)
    
    # Get unique categories and priorities
    categories = sorted([cat for cat in set(t.get('category') for t in todos) if cat])
    priorities = ["All", "High", "Medium", "Low"]
    
    with col2:
        selected_category = st.selectbox("Category", ["All"] + categories)
    
    with col3:
        selected_priority = st.selectbox("Priority", priorities)
    
    # Export button
    st.markdown("---")
    
    if st.button("📥 Export to CSV", use_container_width=False):
        csv_data = export_to_csv(todos)
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name=f"todos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key="download_csv"
        )
    
    st.markdown("---")
    
    # Quick Overview - Bullet Point List
    st.markdown("""
    <div style="margin: 1.5rem 0 1rem 0;">
        <h3 style="color: #6C5CE7; margin: 0;">📝 Quick Overview</h3>
        <p style="color: rgba(248, 249, 250, 0.5); font-size: 0.85rem; margin-top: 0.25rem;">All reminders at a glance</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Collect filtered todos for bullet list
    filtered_todos = []
    now = datetime.now()
    
    for todo in todos:
        # Apply category filter
        if selected_category != "All" and todo.get('category') != selected_category:
            continue
        
        # Apply priority filter
        if selected_priority != "All" and todo.get('priority', 'Medium') != selected_priority:
            continue
        
        # Apply completion filter
        if not show_completed and todo['completed']:
            continue
        
        filtered_todos.append(todo)
    
    # Display bullet point list
    if filtered_todos:
        bullet_list = []
        for todo in filtered_todos:
            # Priority emoji
            priority_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(todo.get('priority', 'Medium'), "🟡")
            
            # Completion status
            status_emoji = "✅" if todo['completed'] else "⭐"
            
            # Parse due date
            due_date_str = todo['due_date'].replace(' ', 'T') if ' ' in todo['due_date'] else todo['due_date']
            due = datetime.fromisoformat(due_date_str)
            due_str = due.strftime('%b %d, %I:%M %p')
            
            # Build bullet
            category_text = f"[{todo.get('category')}]" if todo.get('category') else ""
            bullet = f"{status_emoji} {priority_emoji} **{todo['title']}** {category_text} - Due: {due_str}"
            bullet_list.append(bullet)
        
        # Display as markdown list
        st.markdown("\n".join([f"- {item}" for item in bullet_list]))
    else:
        st.info("No reminders match the current filters.")
    
    st.markdown("---")
    st.markdown("""
    <div style="margin: 1.5rem 0 1rem 0;">
        <h3 style="color: #00D1B2; margin: 0;">📂 Organized View</h3>
        <p style="color: rgba(248, 249, 250, 0.5); font-size: 0.85rem; margin-top: 0.25rem;">Reminders grouped by status</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Separate todos into categories
    overdue = []
    today = []
    upcoming = []
    completed = []
    
    for todo in filtered_todos:
        # Handle both formats: 'T' separator and space separator
        due_date_str = todo['due_date'].replace(' ', 'T') if ' ' in todo['due_date'] else todo['due_date']
        due = datetime.fromisoformat(due_date_str)
        
        if todo['completed']:
            completed.append(todo)
        elif due < now:
            overdue.append(todo)
        elif due.date() == now.date():
            today.append(todo)
        else:
            upcoming.append(todo)
    
    # Display overdue todos
    if overdue:
        st.markdown("""
        <div style="margin: 1.5rem 0 1rem 0;">
            <h3 style="color: #ff6b6b; margin: 0;">🚨 Overdue</h3>
            <p style="color: rgba(248, 249, 250, 0.5); font-size: 0.85rem; margin-top: 0.25rem;">Reminders that need attention</p>
        </div>
        """, unsafe_allow_html=True)
        for todo in overdue:
            display_todo(todo)
    
    # Display today's todos
    if today:
        st.markdown("""
        <div style="margin: 1.5rem 0 1rem 0;">
            <h3 style="color: #00D1B2; margin: 0;">📅 Due Today</h3>
            <p style="color: rgba(248, 249, 250, 0.5); font-size: 0.85rem; margin-top: 0.25rem;">Reminders for today</p>
        </div>
        """, unsafe_allow_html=True)
        for todo in today:
            display_todo(todo)
    
    # Display upcoming todos
    if upcoming:
        st.markdown("""
        <div style="margin: 1.5rem 0 1rem 0;">
            <h3 style="color: #6C5CE7; margin: 0;">📆 Upcoming</h3>
            <p style="color: rgba(248, 249, 250, 0.5); font-size: 0.85rem; margin-top: 0.25rem;">Future reminders</p>
        </div>
        """, unsafe_allow_html=True)
        for todo in upcoming:
            display_todo(todo)
    
    # Display completed todos
    if completed and show_completed:
        st.markdown("""
        <div style="margin: 1.5rem 0 1rem 0;">
            <h3 style="color: #6bcf7f; margin: 0;">✅ Completed</h3>
            <p style="color: rgba(248, 249, 250, 0.5); font-size: 0.85rem; margin-top: 0.25rem;">Finished reminders</p>
        </div>
        """, unsafe_allow_html=True)
        for todo in completed:
            display_todo(todo)

# Configuration section
st.markdown("<br>", unsafe_allow_html=True)
with st.expander("⚙️ Configuration & Setup Guide"):
    st.markdown("""
    <div style="padding: 1rem;">
        <h3 style="color: #00D1B2; margin-top: 0;">📧 Email Notifications</h3>
        <p style="color: rgba(248, 249, 250, 0.7); line-height: 1.6;">
            To enable email reminders, configure these environment variables:
        </p>
        <ul style="color: rgba(248, 249, 250, 0.7); line-height: 1.8;">
            <li><code>SENDER_EMAIL</code> — Your email address</li>
            <li><code>SENDER_PASSWORD</code> — Email password or app-specific password</li>
            <li><code>SMTP_SERVER</code> — SMTP server (default: smtp.gmail.com)</li>
            <li><code>SMTP_PORT</code> — SMTP port (default: 587)</li>
        </ul>
        
        <h3 style="color: #00D1B2; margin-top: 1.5rem;">📱 SMS & WhatsApp Notifications</h3>
        <p style="color: rgba(248, 249, 250, 0.7); line-height: 1.6;">
            To enable SMS and WhatsApp reminders via Twilio, configure:
        </p>
        <ul style="color: rgba(248, 249, 250, 0.7); line-height: 1.8;">
            <li><code>TWILIO_ACCOUNT_SID</code> — Your Twilio Account SID</li>
            <li><code>TWILIO_AUTH_TOKEN</code> — Your Twilio Auth Token</li>
            <li><code>TWILIO_PHONE_NUMBER</code> — Your Twilio phone number (for SMS)</li>
        </ul>
        <p style="color: rgba(248, 249, 250, 0.7); line-height: 1.6; margin-top: 1rem;">
            <strong>For WhatsApp:</strong> Use Twilio's WhatsApp Sandbox for testing. Join the sandbox by sending a WhatsApp message with the code "join &lt;your-sandbox-code&gt;" to +1 415 523 8886. Your sandbox code is shown in your Twilio Console.
        </p>
        
        <h3 style="color: #00D1B2; margin-top: 1.5rem;">⚡ How It Works</h3>
        <p style="color: rgba(248, 249, 250, 0.7); line-height: 1.6;">
            RAAS checks for upcoming reminders every hour. <strong>Automatic reminders are sent for ALL tasks within 24 hours of their due date.</strong> When it's time, you'll receive notifications via your preferred channels (email, SMS, and/or WhatsApp)!
        </p>
    </div>
    """, unsafe_allow_html=True)
