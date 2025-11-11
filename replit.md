# RAAS — Reminder as a Service

## Overview

**RAAS (Reminder as a Service)** is a Streamlit-based task management application for creating, organizing, and tracking todos with automated email, SMS, and WhatsApp reminders. It monitors upcoming tasks and sends timely notifications to ensure users stay organized.

**Tagline:** "Never miss what matters"

**Key Capabilities:**
- Comprehensive Task Management (titles, descriptions, due dates, contacts).
- Customizable reminders via email, SMS, and WhatsApp.
- Support for recurring tasks (daily, weekly, monthly, yearly).
- Task organization by categories and priority levels.
- Filtering options for category, priority, and completion status.
- Export functionality to CSV format.
- Modern dark-themed UI with custom branding.
- FastAPI-based REST API with OpenAPI/Swagger documentation.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

**UI/UX Design:**
- **Branding:** ⚡ RAAS — Reminder as a Service, "Never miss what matters".
- **Design Philosophy:** Modern, calm, professional aesthetic with a dark theme.
- **Color Palette:** Primary (`#6C5CE7`), Accent (`#00D1B2`), Surface (gradient `#0b0b0f` to `#1a1520`), Priority Colors (High: `#ff6b6b`, Medium: `#ffd93d`, Low: `#6bcf7f`), Text (`#F8F9FA`).
- **Visual Elements:** Priority badges, custom-styled section headers, gradient buttons, subtle cards.
- **Navigation:** Account menu in top right corner provides access to Profile, Settings, and Logout via a consolidated menu interface.

**Frontend Architecture:**
- Built with **Streamlit** and custom CSS for an accessible, Python-native web interface.

**REST API Architecture:**
- Implemented with **FastAPI** for programmatic access, providing high performance and automatic OpenAPI/Swagger documentation.
- **Endpoints:** CRUD operations for todos, statistics, and toggling completion status.
- **Authentication:** Layered security model including a mandatory API Key, session token validation via Authorization header (Bearer token only), and database verification for user existence and onboarding. Platform-independent design works on any hosting service.

**Backend Architecture:**
- Monolithic Python application structure with modular components.
- **Data Persistence:** Uses **SQLite** with multi-user schema supporting automatic migrations.
- **Background Job Processing:** **APScheduler** handles periodic checks for upcoming tasks and reminder dispatch (runs every hour).
- **Notification System:** Supports multi-channel delivery via **SMTP (Email)**, **Twilio (SMS)**, and **Twilio (WhatsApp)** with quiet hours protection for SMS/WhatsApp (12am-9:30am).

**Multi-User Architecture:**
- **Platform-Independent Authentication:** Standalone email magic link system - no platform dependencies, works on any hosting service.
- **Magic Link Flow:** Passwordless authentication via one-time email links with secure token generation and 1-hour expiration.
- **Session Management:** 30-day sessions stored in encrypted database with automatic cleanup of expired sessions and tokens.
- **User Isolation:** All CRUD operations strictly filter by internal user ID (UUID).
- **Contact Data Security:** Email/phone/WhatsApp encrypted with Fernet; email also hashed with SHA-256 for secure lookups.
- **Authentication Database:** Dedicated tables for magic links (one-time tokens) and email sessions (persistent user sessions).
- **Onboarding Flow:** First-time users receive magic link, click to verify email, then complete profile setup (name, username, contact info) and consent preferences.
- **User Profile System:** Each user has a unique username and display name, stored in encrypted database.
- **Logout Flow:** Simple logout button clears session from database and browser, redirects to login page. Users log back in by requesting a new magic link.

**Feature Specifications:**
- **Automatic 24-Hour Reminders:** All tasks within 24 hours of their due date automatically trigger reminders.
- **Quiet Hours Protection:** SMS and WhatsApp notifications respect quiet hours (12:00 AM - 9:30 AM) to avoid disturbing sleep. Email notifications continue normally as they're less intrusive. Note: For reminders with both email and SMS/WhatsApp configured, email will be sent during quiet hours while SMS/WhatsApp are skipped. SMS/WhatsApp-only reminders will retry on the next hourly check after 9:30 AM.
- **Auto-Cleanup on Refresh:** Completed tasks are automatically deleted when the app refreshes.
- **Recurring Task Management:** Automatic rescheduling based on daily, weekly, monthly, or yearly frequencies.
- **Categorization and Prioritization:** Tasks can be assigned categories and priority levels.
- **Advanced Filtering:** Users can filter tasks by category, priority, and completion status.
- **Data Export:** Functionality to export todo lists to CSV format.
- **Inline Editing:** Edit forms appear directly at the task location.
- **Personalized Experience:** Dashboard greets users by their stored name for a professional, personalized feel.
- **Smart Contact Management:** Contact information pulled from user profile - no duplicate entry needed when creating reminders.
- **12-Hour Time Format:** Intuitive time input using Hour (1-12), Minute (00-59), and AM/PM selectors with exact minute precision.
- **Horizontal Action Buttons:** Complete, Edit, and Delete buttons displayed below each task with proper spacing to prevent text wrapping.
- **Editable Profile & Settings:** Users can update all personal information (name, username, email, phone, WhatsApp) and notification preferences from both Profile and Settings pages. All changes are validated, encrypted, and persisted to the database with comprehensive error handling. Data persistence verified across page refreshes.
- **Mobile Browser Alarms:** Real-time browser notifications for tasks due within 24 hours on mobile and desktop. Users enable via Settings → Mobile Alarms. Notifications appear 1 hour before task due time (or immediately if less than 1 hour remaining) with vibration alerts, priority indicators, and task details. Works while app is open in a browser tab. Automatically re-schedules on tab focus.

**Mobile Support:**
- Optimized for iPhone and iPad with a touch-friendly interface.
- Installable as a Progressive Web App (PWA) with a manifest.json and Apple-specific meta tags.
- Responsive CSS with media queries for all screen sizes.
- Browser notification support for in-app mobile alarms.

**Authentication Architecture:**
- **Email Magic Links:** Passwordless authentication system that works on any hosting platform.
- **Security Features:** One-time use tokens, 1-hour link expiration, secure token generation with secrets module.
- **Email Templates:** Beautiful HTML email templates with branding and clear call-to-action buttons.
- **Session Security:** Sessions stored with 30-day expiration, automatic cleanup of expired data.
- **Required Environment Variables:**
  - `SENDER_EMAIL`: Gmail address for sending magic link emails
  - `SENDER_PASSWORD`: Gmail app-specific password for SMTP authentication
  - `SESSION_SECRET`: Secret key for session token generation (auto-generated in dev)
  - `ENCRYPTION_KEY`: Fernet key for encrypting contact data (auto-generated in dev)
  - `RAAS_API_KEY`: API authentication key for REST API access (optional in dev)

**Deployment:**
- **Platform-Independent:** Works on any hosting service (Heroku, AWS, Google Cloud, DigitalOcean, Replit, etc.).
- **Deployment Options:** Replit Publishing, Docker Containerization, traditional VPS, and CI/CD with GitHub Actions.
- **Production Requirements:** Set all required environment variables, use HTTPS for secure session tokens, enable API key authentication.

## External Dependencies

**Third-party Services:**
- **Email Delivery:** Gmail SMTP server.
- **SMS Delivery:** Twilio API.
- **WhatsApp Delivery:** Twilio WhatsApp API.

**Python Packages:**
- **Core Framework:** `streamlit`
- **Database:** `sqlite3`
- **Scheduling:** `apscheduler`
- **Email & SMS:** `smtplib`, `email.mime`, `twilio`
- **Export:** `csv`
- **Encryption:** `cryptography` (for Fernet)