import streamlit as st
from datetime import datetime, timedelta
import database
import scheduler
import csv
import io
from fpdf import FPDF

# Initialize database
database.init_db()

# Start the reminder scheduler
scheduler.start_scheduler()

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

# Header with branding
st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
    <h1 style="margin-bottom: 0.5rem;">⚡ RAAS</h1>
    <p style="color: rgba(248, 249, 250, 0.7); font-size: 1.1rem; margin-top: 0;">
        Reminder as a Service — Never miss what matters
    </p>
</div>
""", unsafe_allow_html=True)

# Sidebar for adding/editing todos
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h2 style="margin: 0;">✨ Add Reminder</h2>
        <p style="color: rgba(248, 249, 250, 0.6); font-size: 0.9rem; margin-top: 0.5rem;">
            Never forget what matters
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("add_todo_form", clear_on_submit=True):
        title = st.text_input("Title *", placeholder="e.g., Finish project report")
        description = st.text_area("Description", placeholder="Add details about this task...")
        due_date = st.date_input("Due Date *", min_value=datetime.now().date())
        due_time = st.time_input("Due Time *", value=datetime.now().time())
        
        st.subheader("Reminder Settings")
        st.info("⚡ Auto-reminders sent for all tasks within 24 hours of due date!")
        
        email = st.text_input("Email", placeholder="your@email.com")
        phone = st.text_input("Phone (SMS)", placeholder="+1234567890")
        whatsapp_phone = st.text_input("WhatsApp", placeholder="+1234567890")
        
        st.caption("📧 Email reminders require SMTP configuration")
        st.caption("📱 SMS & WhatsApp require Twilio credentials")
        
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
                # Combine date and time
                due_datetime = datetime.combine(due_date, due_time)
                database.add_todo(
                    title=title,
                    description=description,
                    due_date=due_datetime.isoformat(),
                    email=email,
                    phone=phone,
                    whatsapp_phone=whatsapp_phone,
                    reminder_hours=24,  # Auto-reminder set to 24 hours
                    is_recurring=is_recurring,
                    recurrence_frequency=recurrence_frequency,
                    recurrence_interval=recurrence_interval,
                    category=category if category else None,
                    priority=priority
                )
                st.success("Todo added successfully!")
                st.rerun()
            else:
                st.error("Please fill in the required fields (Title and Due Date)")

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

def export_to_pdf(todos):
    """Export todos to PDF format."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, 'Todo List Export', ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 10, f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M")}', ln=True)
    pdf.ln(5)
    
    # Add todos
    for todo in todos:
        pdf.set_font("Arial", 'B', 12)
        priority_text = {'High': '[HIGH]', 'Medium': '[MED]', 'Low': '[LOW]'}.get(todo.get('priority', 'Medium'), '[MED]')
        status_text = '[DONE]' if todo['completed'] else '[TODO]'
        
        title_line = f"{status_text} {priority_text} {todo['title']}"
        pdf.cell(0, 10, title_line, ln=True)
        
        pdf.set_font("Arial", '', 10)
        if todo.get('category'):
            pdf.cell(0, 6, f"Category: {todo['category']}", ln=True)
        
        pdf.cell(0, 6, f"Due: {todo['due_date']}", ln=True)
        
        if todo.get('description'):
            pdf.multi_cell(0, 6, f"Description: {todo['description']}")
        
        if todo.get('is_recurring'):
            freq = todo.get('recurrence_frequency', 'days')
            interval = todo.get('recurrence_interval', 1)
            pdf.cell(0, 6, f"Recurring: Every {interval} {freq}", ln=True)
        
        if todo.get('email') or todo.get('phone'):
            contact = []
            if todo.get('email'):
                contact.append(f"Email: {todo['email']}")
            if todo.get('phone'):
                contact.append(f"Phone: {todo['phone']}")
            pdf.cell(0, 6, ' | '.join(contact), ln=True)
        
        pdf.ln(3)
    
    # output() returns bytearray in fpdf2, convert to bytes for streamlit
    return bytes(pdf.output())

def display_todo(todo):
    """Display a single todo item with actions or edit form."""
    # Check if this todo is being edited
    if 'editing_todo' in st.session_state and st.session_state.editing_todo == todo['id']:
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
            edit_due_time = st.time_input("Due Time", value=due_datetime.time())
            
            st.caption("⚡ Auto-reminders sent when task is within 24 hours of due date")
            
            edit_email = st.text_input("Email", value=todo['email'] or "")
            edit_phone = st.text_input("Phone (SMS)", value=todo['phone'] or "")
            edit_whatsapp_phone = st.text_input("WhatsApp", value=todo.get('whatsapp_phone') or "")
            
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
                    edit_due_datetime = datetime.combine(edit_due_date, edit_due_time)
                    database.update_todo(
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
                    st.success("Reminder updated!")
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
        col1, col2, col3 = st.columns([4, 2, 1])
        
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
        
        with col3:
            # Action buttons stacked vertically for compact layout
            if st.button("✓" if not todo['completed'] else "↶", key=f"complete_{todo['id']}", help="Toggle complete", use_container_width=True):
                database.toggle_complete(todo['id'])
                st.rerun()
            
            if st.button("✏️ Edit", key=f"edit_{todo['id']}", help="Edit reminder", use_container_width=True):
                st.session_state.editing_todo = todo['id']
                st.rerun()
            
            if st.button("🗑️ Delete", key=f"delete_{todo['id']}", help="Delete reminder", use_container_width=True):
                database.delete_todo(todo['id'])
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

# Get all todos
todos = database.get_all_todos()

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
    
    # Export buttons
    st.markdown("---")
    col_exp1, col_exp2, col_exp3 = st.columns([1, 1, 4])
    
    with col_exp1:
        if st.button("📥 Export to CSV", use_container_width=True):
            csv_data = export_to_csv(todos)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"todos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="download_csv"
            )
    
    with col_exp2:
        if st.button("📄 Export to PDF", use_container_width=True):
            pdf_data = export_to_pdf(todos)
            st.download_button(
                label="Download PDF",
                data=pdf_data,
                file_name=f"todos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                key="download_pdf"
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
