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
- Export functionality to CSV or PDF.
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

**Frontend Architecture:**
- Built with **Streamlit** and custom CSS for an accessible, Python-native web interface.

**REST API Architecture:**
- Implemented with **FastAPI** for programmatic access, providing high performance and automatic OpenAPI/Swagger documentation.
- **Endpoints:** CRUD operations for todos, statistics, and toggling completion status.
- **Authentication:** Layered security model including a mandatory API Key, Replit Auth Headers, and database verification for user existence and onboarding. Designed for internal/Replit deployment.

**Backend Architecture:**
- Monolithic Python application structure with modular components.
- **Data Persistence:** Uses **SQLite** with multi-user schema supporting automatic migrations.
- **Background Job Processing:** **APScheduler** handles periodic checks for upcoming tasks and reminder dispatch.
- **Notification System:** Supports multi-channel delivery via **SMTP (Email)**, **Twilio (SMS)**, and **Twilio (WhatsApp)**.

**Multi-User Architecture:**
- **Dual-ID System:** Each user has an internal RAAS UUID and an external Replit ID for authentication lookup.
- **Authentication Flow:** Integrates with Replit Auth, looking up users by `X-Replit-User-Id` to retrieve the internal UUID for all database operations.
- **User Isolation:** All CRUD operations strictly filter by internal user ID.
- **Contact Data Security:** Email/phone/WhatsApp encrypted with Fernet; email also hashed with SHA-256.
- **Onboarding Flow:** First-time users complete contact info and consent preferences.

**Feature Specifications:**
- **Automatic 24-Hour Reminders:** All tasks within 24 hours of their due date automatically trigger reminders.
- **Auto-Cleanup on Refresh:** Completed tasks are automatically deleted when the app refreshes.
- **Recurring Task Management:** Automatic rescheduling based on daily, weekly, monthly, or yearly frequencies.
- **Categorization and Prioritization:** Tasks can be assigned categories and priority levels.
- **Advanced Filtering:** Users can filter tasks by category, priority, and completion status.
- **Data Export:** Functionality to export todo lists to CSV and PDF formats.
- **Inline Editing:** Edit forms appear directly at the task location.
- **Horizontal Action Buttons:** Complete, Edit, and Delete buttons displayed below each task.

**Mobile Support:**
- Optimized for iPhone and iPad with a touch-friendly interface.
- Installable as a Progressive Web App (PWA) with a manifest.json and Apple-specific meta tags.
- Responsive CSS with media queries for all screen sizes.

**Deployment:**
- Supports Replit Publishing (recommended), Docker Containerization, and CI/CD with GitHub Actions.

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
- **Export:** `csv`, `fpdf2`
- **Encryption:** `cryptography` (for Fernet)