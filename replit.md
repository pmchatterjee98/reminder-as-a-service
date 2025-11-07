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
- **Typography:** Default Streamlit fonts with custom sizing and color hierarchy.

**Frontend Architecture:**
- Built with **Streamlit** and custom CSS for an accessible, Python-native web interface.
- Uses a sidebar for forms and a main area for task lists, with a "wide" layout.

**REST API Architecture:**
- Implemented with **FastAPI** for programmatic access, providing high performance and automatic OpenAPI/Swagger documentation.
- **Endpoints:** CRUD operations for todos, statistics, and toggling completion status.
- **Authentication:** Currently open (planned for production).

**Backend Architecture:**
- Monolithic Python application structure with modular components for database, notifications, and scheduling.
- **Data Persistence:** Uses **SQLite** with a single `todos` table, supporting automatic schema migrations.
- **Background Job Processing:** **APScheduler** handles periodic checks for upcoming tasks and reminder dispatch.
- **Notification System:** Supports multi-channel delivery via **SMTP (Email)**, **Twilio (SMS)**, and **Twilio (WhatsApp)**, with environment variable-based configuration for credentials.

**Feature Specifications:**
- **Customizable Reminder Intervals:** Options from 1 hour to 7 days before the due date.
- **Recurring Task Management:** Automatic rescheduling based on daily, weekly, monthly, or yearly frequencies.
- **Categorization and Prioritization:** Tasks can be assigned categories and priority levels (High, Medium, Low).
- **Advanced Filtering:** Users can filter tasks by category, priority, and completion status.
- **Data Export:** Functionality to export todo lists to CSV and PDF formats with timestamped filenames.

## External Dependencies

**Third-party Services:**
- **Email Delivery:** Gmail SMTP server for sending email reminders.
- **SMS Delivery:** Twilio API for sending SMS reminders.
- **WhatsApp Delivery:** Twilio WhatsApp API for sending WhatsApp reminders.

**Python Packages:**
- **Core Framework:** `streamlit`
- **Database:** `sqlite3`
- **Scheduling:** `apscheduler`
- **Email & SMS:** `smtplib`, `email.mime`, `twilio`
- **Export:** `csv`, `fpdf2`
- **Utilities:** `datetime`, `os`, `typing`, `io`