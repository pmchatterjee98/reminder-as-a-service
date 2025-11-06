import streamlit as st
from datetime import datetime, timedelta
import database
import scheduler

# Initialize database
database.init_db()

# Start the reminder scheduler
scheduler.start_scheduler()

# Page configuration
st.set_page_config(
    page_title="Todo List with Reminders",
    page_icon="✅",
    layout="wide"
)

st.title("✅ Todo List with Reminders")
st.markdown("Manage your tasks and receive email and SMS reminders before due dates!")

# Sidebar for adding/editing todos
with st.sidebar:
    st.header("Add New Todo")
    
    with st.form("add_todo_form", clear_on_submit=True):
        title = st.text_input("Title *", placeholder="e.g., Finish project report")
        description = st.text_area("Description", placeholder="Add details about this task...")
        due_date = st.date_input("Due Date *", min_value=datetime.now().date())
        due_time = st.time_input("Due Time *", value=datetime.now().time())
        
        st.subheader("Reminder Settings")
        reminder_hours = st.selectbox(
            "Send reminder before due date",
            options=[1, 2, 6, 12, 24, 48, 72, 168],
            index=4,
            format_func=lambda x: f"{x} hour{'s' if x != 1 else ''}" if x < 24 else f"{x//24} day{'s' if x//24 != 1 else ''}"
        )
        email = st.text_input("Email", placeholder="your@email.com")
        phone = st.text_input("Phone", placeholder="+1234567890")
        
        st.caption("📧 Email reminders require SMTP configuration")
        st.caption("📱 SMS reminders require Twilio credentials")
        
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
                    reminder_hours=reminder_hours,
                    is_recurring=is_recurring,
                    recurrence_frequency=recurrence_frequency,
                    recurrence_interval=recurrence_interval
                )
                st.success("Todo added successfully!")
                st.rerun()
            else:
                st.error("Please fill in the required fields (Title and Due Date)")

def display_todo(todo):
    """Display a single todo item with actions."""
    # Handle both formats: 'T' separator and space separator
    due_date_str = todo['due_date'].replace(' ', 'T') if ' ' in todo['due_date'] else todo['due_date']
    due = datetime.fromisoformat(due_date_str)
    now = datetime.now()
    
    # Determine status color
    if todo['completed']:
        status_color = "green"
        status_icon = "✅"
    elif due < now:
        status_color = "red"
        status_icon = "🚨"
    else:
        status_color = "blue"
        status_icon = "📌"
    
    with st.container():
        col1, col2, col3, col4 = st.columns([0.5, 3, 1.5, 1])
        
        with col1:
            st.markdown(f"### {status_icon}")
        
        with col2:
            if todo['completed']:
                st.markdown(f"~~**{todo['title']}**~~")
            else:
                st.markdown(f"**{todo['title']}**")
            
            if todo['description']:
                st.caption(todo['description'])
        
        with col3:
            st.caption(f"📅 Due: {due.strftime('%Y-%m-%d %H:%M')}")
            
            if todo.get('is_recurring'):
                freq = todo.get('recurrence_frequency', 'days')
                interval = todo.get('recurrence_interval', 1)
                st.caption(f"🔁 Repeats every {interval} {freq}")
            
            if todo['email']:
                st.caption(f"📧 {todo['email']}")
            if todo['phone']:
                st.caption(f"📱 {todo['phone']}")
            if todo['reminder_sent']:
                st.caption("🔔 Reminder sent")
        
        with col4:
            if st.button("✓" if not todo['completed'] else "↶", key=f"complete_{todo['id']}", help="Toggle complete"):
                database.toggle_complete(todo['id'])
                st.rerun()
            
            if st.button("✏️", key=f"edit_{todo['id']}", help="Edit"):
                st.session_state.editing_todo = todo['id']
                st.rerun()
            
            if st.button("🗑️", key=f"delete_{todo['id']}", help="Delete"):
                database.delete_todo(todo['id'])
                st.rerun()
        
        st.divider()

# Main content area
st.header("Your Todos")

# Get all todos
todos = database.get_all_todos()

if not todos:
    st.info("No todos yet! Add your first task using the form on the left.")
else:
    # Filter options
    col1, col2 = st.columns([1, 4])
    with col1:
        show_completed = st.checkbox("Show completed", value=True)
    
    # Separate todos into categories
    overdue = []
    today = []
    upcoming = []
    completed = []
    
    now = datetime.now()
    
    for todo in todos:
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
        st.subheader("🚨 Overdue")
        for todo in overdue:
            display_todo(todo)
    
    # Display today's todos
    if today:
        st.subheader("📅 Due Today")
        for todo in today:
            display_todo(todo)
    
    # Display upcoming todos
    if upcoming:
        st.subheader("📆 Upcoming")
        for todo in upcoming:
            display_todo(todo)
    
    # Display completed todos
    if completed and show_completed:
        st.subheader("✅ Completed")
        for todo in completed:
            display_todo(todo)

# Edit todo modal
if 'editing_todo' in st.session_state and st.session_state.editing_todo:
    todo_id = st.session_state.editing_todo
    todo = database.get_todo_by_id(todo_id)
    
    if todo:
        st.header("Edit Todo")
        
        # Handle both formats: 'T' separator and space separator
        due_date_str = todo['due_date'].replace(' ', 'T') if ' ' in todo['due_date'] else todo['due_date']
        due_datetime = datetime.fromisoformat(due_date_str)
        
        with st.form("edit_todo_form"):
            edit_title = st.text_input("Title", value=todo['title'])
            edit_description = st.text_area("Description", value=todo['description'] or "")
            edit_due_date = st.date_input("Due Date", value=due_datetime.date())
            edit_due_time = st.time_input("Due Time", value=due_datetime.time())
            
            current_reminder_hours = todo.get('reminder_hours', 24)
            reminder_options = [1, 2, 6, 12, 24, 48, 72, 168]
            default_index = reminder_options.index(current_reminder_hours) if current_reminder_hours in reminder_options else 4
            
            edit_reminder_hours = st.selectbox(
                "Send reminder before due date",
                options=reminder_options,
                index=default_index,
                format_func=lambda x: f"{x} hour{'s' if x != 1 else ''}" if x < 24 else f"{x//24} day{'s' if x//24 != 1 else ''}"
            )
            edit_email = st.text_input("Email", value=todo['email'] or "")
            edit_phone = st.text_input("Phone", value=todo['phone'] or "")
            
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
                if st.form_submit_button("Save Changes", use_container_width=True):
                    edit_due_datetime = datetime.combine(edit_due_date, edit_due_time)
                    database.update_todo(
                        todo_id=todo_id,
                        title=edit_title or "",
                        description=edit_description or "",
                        due_date=edit_due_datetime.isoformat(),
                        email=edit_email or "",
                        phone=edit_phone or "",
                        reminder_hours=edit_reminder_hours,
                        is_recurring=edit_is_recurring,
                        recurrence_frequency=edit_recurrence_frequency if edit_is_recurring else None,
                        recurrence_interval=edit_recurrence_interval if edit_is_recurring else None
                    )
                    del st.session_state.editing_todo
                    st.success("Todo updated!")
                    st.rerun()
            
            with col2:
                if st.form_submit_button("Cancel", use_container_width=True):
                    del st.session_state.editing_todo
                    st.rerun()

# Configuration section
with st.expander("⚙️ Reminder Configuration"):
    st.markdown("""
    ### Email Configuration
    To enable email reminders, set these environment variables:
    - `SENDER_EMAIL`: Your email address
    - `SENDER_PASSWORD`: Your email password or app-specific password
    - `SMTP_SERVER`: SMTP server (default: smtp.gmail.com)
    - `SMTP_PORT`: SMTP port (default: 587)
    
    ### SMS Configuration
    To enable SMS reminders, set these environment variables:
    - `TWILIO_ACCOUNT_SID`: Your Twilio Account SID
    - `TWILIO_AUTH_TOKEN`: Your Twilio Auth Token
    - `TWILIO_PHONE_NUMBER`: Your Twilio phone number
    
    Reminders are checked every hour. Each todo can have its own custom reminder interval (1 hour to 7 days before due date).
    """)
