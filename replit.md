# RAAS — Reminder as a Service

## Overview

**⚡ RAAS (Reminder as a Service)** is a comprehensive task management application built with Streamlit that allows users to create, organize, and track todos with automated email, SMS, and WhatsApp reminders. The application monitors upcoming tasks and sends notifications before due dates to help users stay on top of their responsibilities.

**Tagline:** "Never miss what matters"

**Key Features:**
- **Task Management**: Create tasks with titles, descriptions, due dates/times, and contact information
- **Smart Reminders**: Customizable reminder intervals (1 hour to 7 days before due date) via email, SMS, and WhatsApp
- **Recurring Tasks**: Automatic rescheduling of recurring tasks (daily, weekly, monthly, yearly)
- **Organization**: Categories and priority levels (High/Medium/Low) with color-coded indicators
- **Filtering**: Filter todos by category, priority, and completion status
- **Export**: Export todo list to CSV or PDF format with timestamped filenames
- **Modern UI**: Dark-themed interface with custom RAAS branding and color palette
- **REST API**: Comprehensive FastAPI-based REST API with automatic OpenAPI/Swagger documentation

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
**Framework: Streamlit with Custom CSS**
- **Problem**: Need an accessible, web-based interface for task management
- **Solution**: Streamlit provides a Python-native way to build interactive web applications without frontend complexity
- **Rationale**: Quick development, built-in form handling, and automatic UI updates make it ideal for rapid prototyping and simple CRUD operations
- **Pros**: Minimal code, automatic reactivity, Python-only development
- **Cons**: Limited customization, not suitable for complex UX requirements

The interface uses a sidebar form for adding/editing todos and the main area for displaying task lists. Layout is configured as "wide" to maximize screen real estate.

### REST API Architecture
**Framework: FastAPI with Automatic OpenAPI Documentation**
- **Problem**: Need programmatic access to RAAS functionality for integrations and automation
- **Solution**: FastAPI REST API with comprehensive endpoints for todo management
- **Rationale**: FastAPI provides automatic Swagger/OpenAPI documentation, high performance, and modern async capabilities
- **Pros**: Automatic API docs, data validation with Pydantic, fast performance, type safety
- **Cons**: Requires additional server process

**API Endpoints:**
- **Base URL**: `http://localhost:8000` (development)
- **Documentation**: `http://localhost:8000/docs` (Swagger UI)
- **Alternative Docs**: `http://localhost:8000/redoc` (ReDoc)
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

**Available Endpoints:**
- `GET /` - API information and service metadata
- `GET /todos` - List all todos with optional filtering (category, priority, completed, limit)
- `GET /todos/{id}` - Get a specific todo by ID
- `POST /todos` - Create a new todo
- `PUT /todos/{id}` - Update an existing todo
- `DELETE /todos/{id}` - Delete a todo
- `POST /todos/{id}/toggle-complete` - Toggle completion status
- `GET /stats` - Get statistics about todos (totals, priorities, categories)

**Authentication**: Currently open (add authentication in production)

### UI/UX Design System
**RAAS Brand Identity**
- **Branding**: ⚡ RAAS — Reminder as a Service
- **Tagline**: "Never miss what matters"
- **Design Philosophy**: Modern, calm, professional aesthetic with dark theme

**Color Palette**
- **Primary**: `#6C5CE7` (Indigo/Violet) - Used for main branding, buttons, and key UI elements
- **Accent**: `#00D1B2` (Teal) - Used for section headers, highlights, and interactive elements
- **Surface**: `#0b0b0f` to `#1a1520` gradient - Dark background with subtle purple gradient
- **Priority Colors**:
  - High: `#ff6b6b` (Red/Coral)
  - Medium: `#ffd93d` (Yellow)
  - Low: `#6bcf7f` (Green)
- **Text**: `#F8F9FA` (Off-white) with varying opacity levels for hierarchy

**Visual Elements**
- **Priority Badges**: HTML `<span>` elements with colored backgrounds and rounded corners
- **Section Headers**: Custom styled with RAAS colors, emojis, and descriptive subtitles
- **Buttons**: Gradient backgrounds with hover effects and full-width styling
- **Cards**: Subtle borders, dark backgrounds with slight transparency
- **Forms**: Organized layout with clear visual hierarchy and spacing
- **Configuration**: Expandable section with formatted HTML content

**Typography**
- Default Streamlit fonts with custom sizing and color hierarchy
- Headers use gradient colors for visual interest
- Descriptions use reduced opacity for secondary information
- Monospace font for configuration variable names

### Backend Architecture
**Pattern: Monolithic Python Application**
- **Problem**: Need to handle task persistence, scheduled notifications, and user interactions
- **Solution**: Single Python application with modular components (`database.py`, `notifications.py`, `scheduler.py`, `app.py`)
- **Rationale**: Simplicity for a small-scale application; easier to deploy and maintain
- **Pros**: Simple deployment, no API overhead, direct function calls
- **Cons**: Harder to scale horizontally, tightly coupled components

### Data Persistence
**Database: SQLite**
- **Problem**: Need persistent storage for todo items and reminder state
- **Solution**: SQLite with a single `todos` table with migration support
- **Rationale**: Serverless, zero-configuration database that works well for single-user or small-scale applications
- **Schema Design**: Flat table structure with comprehensive fields:
  - Task details: `title`, `description`, `due_date`, `created_at`
  - Contact information: `email`, `phone`
  - State tracking: `completed`, `reminder_sent`
  - Reminder settings: `reminder_hours` (customizable: 1, 2, 6, 12, 24, 48, 72, 168 hours)
  - Recurrence: `is_recurring`, `recurrence_frequency`, `recurrence_interval`
  - Organization: `category`, `priority` (High/Medium/Low)
- **Migration Support**: Automatic schema updates using `ALTER TABLE` to add new columns without data loss
- **Pros**: No external dependencies, file-based portability, ACID compliance, automatic migrations
- **Cons**: Limited concurrency, not suitable for high-traffic scenarios

### Background Job Processing
**Scheduler: APScheduler (Background)**
- **Problem**: Need to check for upcoming tasks periodically and send reminders automatically
- **Solution**: BackgroundScheduler with interval-based triggers
- **Implementation**: Runs `check_and_send_reminders()` function at regular intervals (designed for hourly checks)
- **Rationale**: In-process scheduler eliminates need for external job queue systems
- **Pros**: Simple setup, runs in same process as web app
- **Cons**: Restarts when app restarts, not suitable for distributed systems

### Notification System
**Multi-channel Delivery**
- **Problem**: Users need reminders via different communication channels
- **Solution**: Separate email, SMS, and WhatsApp notification functions with independent success tracking
- **Email**: SMTP-based using Python's `smtplib` and `email.mime`
- **SMS**: Twilio integration with professional RAAS branding
- **WhatsApp**: Twilio WhatsApp API integration with RAAS branding
- **Rationale**: Flexibility for users to choose preferred notification method(s)
- **Configuration**: Environment variable-based configuration for credentials (SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER)
- **Error Handling**: Graceful degradation - if one channel fails, the others can still succeed

## External Dependencies

### Third-party Services

**Email Delivery (Gmail via SMTP)**
- **Service**: Gmail SMTP server
- **Status**: ✅ Fully configured and operational
- **Configuration**: Configured with `SENDER_EMAIL` and `SENDER_PASSWORD` (Gmail App Password) environment variables
- **Port**: 587 (TLS)
- **Purpose**: Sending email reminders to users
- **Subject Format**: "⚡ RAAS Reminder: {task_title}"
- **Body**: Professional formatted email with RAAS branding

**SMS Delivery (Twilio)**
- **Service**: Twilio API
- **Status**: ✅ Fully configured and operational
- **Purpose**: Sending SMS reminders to users
- **Configuration**: Configured with `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and `TWILIO_PHONE_NUMBER` environment variables
- **Usage**: Optional - users can choose email, SMS, WhatsApp, or any combination of notification channels
- **Message Format**: "⚡ RAAS Reminder\n\n📌 {task}\n⏰ Due: {date}\n\nNever miss what matters!"

**WhatsApp Delivery (Twilio)**
- **Service**: Twilio WhatsApp API
- **Status**: ✅ Fully configured and operational
- **Purpose**: Sending WhatsApp reminders to users
- **Configuration**: Uses the same Twilio credentials as SMS (`TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`)
- **Testing**: Requires joining Twilio's WhatsApp Sandbox - send "join <sandbox-code>" to whatsapp:+14155238886
- **Usage**: Optional - users can choose any combination of email, SMS, and WhatsApp notifications
- **Message Format**: "⚡ RAAS Reminder\n\n📌 {task}\n⏰ Due: {date}\n\nNever miss what matters!"
- **Database Field**: `whatsapp_phone` column in todos table stores WhatsApp phone numbers

### Python Packages

**Core Framework**
- `streamlit`: Web application framework and UI

**Database**
- `sqlite3`: Built-in Python library for SQLite database operations

**Scheduling**
- `apscheduler`: Background task scheduling for reminder checks

**Email & SMS**
- `smtplib`: Built-in SMTP client
- `email.mime`: Email message construction
- `twilio`: Twilio SDK for SMS notifications

**Export**
- `csv`: Built-in CSV file generation
- `fpdf2`: PDF document generation with formatting

**Utilities**
- `datetime`: Date and time operations for due date handling
- `os`: Environment variable access for configuration
- `typing`: Type hints for better code documentation
- `io`: In-memory file operations for exports

## Recent Changes

### November 7, 2025 - Latest Updates

**WhatsApp Integration**
- **WhatsApp Notifications**: Full integration with Twilio WhatsApp API for sending reminders
- **Database Migration**: Added `whatsapp_phone` column to todos table with automatic migration
- **UI Updates**: Added WhatsApp phone input fields to both add and edit forms in Streamlit app
- **API Updates**: Updated REST API models and endpoints to support WhatsApp phone numbers
- **Scheduler Integration**: Enhanced scheduler to send WhatsApp reminders alongside email and SMS
- **Multi-channel Support**: Users can now choose any combination of email, SMS, and WhatsApp notifications
- **Documentation**: Updated configuration guide with WhatsApp sandbox setup instructions

**Notification System Activation**
- **Email Notifications**: Fully configured with Gmail SMTP using app password
- **SMS Notifications**: Fully configured with Twilio API credentials
- **RAAS Branding**: Updated email and SMS messages with professional RAAS branding
- **Security**: All credentials stored securely as Replit Secrets
- **Testing**: Created test_notifications.py script for manual testing

**REST API Addition**
- **REST API with Swagger**: Added comprehensive FastAPI-based REST API with automatic OpenAPI/Swagger documentation
- **API Endpoints**: Full CRUD operations for todos (GET, POST, PUT, DELETE) plus statistics endpoint
- **Interactive Documentation**: Swagger UI at `/docs` and ReDoc at `/redoc` for testing and documentation
- **Data Validation**: Pydantic models for request/response validation with automatic schema generation
- **Filtering Support**: Query parameters for filtering by category, priority, completion status, and limiting results
- **CORS Enabled**: Cross-origin resource sharing configured for frontend integrations
- **Dual Server Setup**: API runs on port 8000, Streamlit app on port 5000

### November 6, 2025 - Latest Update
- **RAAS Rebranding**: Complete rebrand to "RAAS — Reminder as a Service" with new visual identity
- **Custom Dark Theme**: Implemented dark theme with RAAS color palette (indigo primary, teal accent)
- **UI Redesign**: Modern interface with custom CSS, styled headers, and gradient backgrounds
- **HTML Priority Badges**: Replaced emoji indicators with styled HTML badges using RAAS colors
- **Enhanced Visual Hierarchy**: Improved section organization with colored headers and descriptions
- **Styled Configuration Section**: Reformatted setup guide with RAAS branding and clear organization
- **Button Styling**: Added gradient backgrounds and hover effects to all buttons
- **Form Improvements**: Better layout and visual organization for add/edit forms

### November 6, 2025 - Earlier Updates
- **Customizable Reminder Intervals**: Added `reminder_hours` field to database with options from 1 hour to 7 days
- **Recurring Tasks**: Implemented automatic rescheduling with support for daily, weekly, monthly, and yearly recurrence
- **Categories and Priorities**: Added category field and priority levels (High/Medium/Low) with color-coded indicators
- **Advanced Filtering**: Added dropdown filters for category and priority with "All" option
- **Export Functionality**: Implemented CSV and PDF export with comprehensive todo data and timestamped filenames
- **Database Migration**: Added automatic schema migration support to handle new fields without data loss