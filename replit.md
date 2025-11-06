# Todo List with Reminders

## Overview

This is a task management application built with Streamlit that allows users to create todos with automated email and SMS reminders. The application monitors upcoming tasks and sends notifications before due dates to help users stay on top of their responsibilities. Users can add tasks with titles, descriptions, due dates/times, and contact information for receiving reminders.

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
- **Solution**: SQLite with a single `todos` table
- **Rationale**: Serverless, zero-configuration database that works well for single-user or small-scale applications
- **Schema Design**: Flat table structure with fields for task details (title, description, due_date), contact information (email, phone), and state tracking (completed, reminder_sent, created_at)
- **Pros**: No external dependencies, file-based portability, ACID compliance
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
- **Status**: Integration planned but not fully implemented
- **Purpose**: Sending SMS reminders to users
- **Configuration**: Will require Twilio account credentials

### Python Packages

**Core Framework**
- `streamlit`: Web application framework and UI

**Database**
- `sqlite3`: Built-in Python library for SQLite database operations

**Scheduling**
- `apscheduler`: Background task scheduling for reminder checks

**Email**
- `smtplib`: Built-in SMTP client
- `email.mime`: Email message construction

**Utilities**
- `datetime`: Date and time operations for due date handling
- `os`: Environment variable access for configuration
- `typing`: Type hints for better code documentation