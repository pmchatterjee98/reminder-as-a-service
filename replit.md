# Todo List with Reminders

## Overview

This is a comprehensive task management application built with Streamlit that allows users to create, organize, and track todos with automated email and SMS reminders. The application monitors upcoming tasks and sends notifications before due dates to help users stay on top of their responsibilities.

**Key Features:**
- **Task Management**: Create tasks with titles, descriptions, due dates/times, and contact information
- **Smart Reminders**: Customizable reminder intervals (1 hour to 7 days before due date) via email and SMS
- **Recurring Tasks**: Automatic rescheduling of recurring tasks (daily, weekly, monthly, yearly)
- **Organization**: Categories and priority levels (High/Medium/Low) with color-coded indicators
- **Filtering**: Filter todos by category, priority, and completion status
- **Export**: Export todo list to CSV or PDF format with timestamped filenames
- **Visual Status**: Color-coded priority indicators and status icons for better task visibility

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
**Framework: Streamlit**
- **Problem**: Need an accessible, web-based interface for task management
- **Solution**: Streamlit provides a Python-native way to build interactive web applications without frontend complexity
- **Rationale**: Quick development, built-in form handling, and automatic UI updates make it ideal for rapid prototyping and simple CRUD operations
- **Pros**: Minimal code, automatic reactivity, Python-only development
- **Cons**: Limited customization, not suitable for complex UX requirements

The interface uses a sidebar form for adding/editing todos and the main area for displaying task lists. Layout is configured as "wide" to maximize screen real estate.

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
- **Solution**: Separate email and SMS notification functions with independent success tracking
- **Email**: SMTP-based using Python's `smtplib` and `email.mime`
- **SMS**: Twilio integration (implementation in progress)
- **Rationale**: Flexibility for users to choose preferred notification method
- **Configuration**: Environment variable-based configuration for credentials (SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD)
- **Error Handling**: Graceful degradation - if one channel fails, the other can still succeed

## External Dependencies

### Third-party Services

**Email Delivery (SMTP)**
- **Service**: Configurable SMTP server (default: Gmail)
- **Configuration**: Requires `SENDER_EMAIL` and `SENDER_PASSWORD` environment variables
- **Port**: 587 (TLS)
- **Purpose**: Sending email reminders to users

**SMS Delivery (Twilio)**
- **Service**: Twilio API
- **Status**: Fully implemented and ready to use
- **Purpose**: Sending SMS reminders to users
- **Configuration**: Requires `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and `TWILIO_PHONE_NUMBER` environment variables
- **Usage**: Optional - users can choose email-only, SMS-only, or both notification channels

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

### November 6, 2025
- **Customizable Reminder Intervals**: Added `reminder_hours` field to database with options from 1 hour to 7 days
- **Recurring Tasks**: Implemented automatic rescheduling with support for daily, weekly, monthly, and yearly recurrence
- **Categories and Priorities**: Added category field and priority levels (High/Medium/Low) with color-coded emoji indicators (🔴/🟡/🟢)
- **Advanced Filtering**: Added dropdown filters for category and priority with "All" option
- **Export Functionality**: Implemented CSV and PDF export with comprehensive todo data and timestamped filenames
- **Database Migration**: Added automatic schema migration support to handle new fields without data loss
- **UI Enhancements**: Improved visual organization with priority indicators and category labels