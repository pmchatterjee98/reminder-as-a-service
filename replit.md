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

## Mobile Support

**Progressive Web App (PWA):**
- Optimized for iPhone and iPad with touch-friendly interface
- Installable on iOS home screen for native app experience
- Responsive CSS with media queries for all screen sizes
- Touch-optimized buttons (44px minimum following iOS HIG)
- Form inputs sized to prevent auto-zoom on mobile
- PWA manifest.json for installability
- Apple-specific meta tags for home screen integration
- Works offline for viewing existing reminders

## Deployment

RAAS supports multiple deployment options:

**Option 1: Replit Publishing (Recommended)**
- Built-in Autoscale deployment with automatic scaling
- Custom domain support with automatic SSL/TLS
- One-click deployment from Replit workspace
- Cost-effective starting at $7/month

**Option 2: Docker Containerization**
- Multi-container setup with Docker Compose
- Separate containers for Streamlit app and FastAPI backend
- Deployable to any cloud provider (AWS, Azure, DigitalOcean, etc.)
- Production-ready with health checks and non-root users

**Option 3: CI/CD with GitHub Actions**
- Automated testing pipeline (linting, Docker builds)
- Continuous deployment to cloud servers
- Docker image publishing to Docker Hub
- SSH-based deployment to production servers

See `DEPLOYMENT.md` for detailed instructions on all deployment options.

## Recent Changes

**Mobile Optimization & PWA** (November 2025)
- Mobile-responsive CSS with media queries for optimal viewing on iPhone/iPad
- Touch optimization with 44px minimum button sizes (iOS HIG standards)
- PWA manifest.json for Progressive Web App installability
- iOS-specific meta tags for home screen installation
- No-zoom form inputs (16px+ font size prevents iOS auto-zoom)
- Generated custom lightning bolt app icon
- Comprehensive mobile guide documentation (MOBILE_GUIDE.md)
- Updated Streamlit config with RAAS theme colors

**Docker & CI/CD Setup** (November 2025)
- Dockerfiles for Streamlit app and FastAPI API
- Docker Compose multi-container orchestration with health checks
- GitHub Actions CI pipeline for automated testing and Docker builds
- GitHub Actions CD pipeline for Docker Hub publishing and SSH deployment
- Comprehensive deployment guide for all options
- Production-ready containers with non-root users and security best practices

**WhatsApp Integration** (November 2025)
- Full Twilio WhatsApp API integration for sending reminders
- Database migration added `whatsapp_phone` column to todos table
- UI updates with WhatsApp phone input fields in add/edit forms
- API updates supporting WhatsApp phone numbers in all endpoints
- Scheduler enhanced to send WhatsApp reminders alongside email and SMS
- Multi-channel support: users can choose any combination of notifications

**REST API Addition** (November 2025)
- Comprehensive FastAPI-based REST API with Swagger documentation
- Full CRUD operations for todos (GET, POST, PUT, DELETE)
- Statistics endpoint for dashboard metrics
- Toggle completion endpoint for quick status updates
- Automatic OpenAPI/Swagger UI at /docs endpoint

**Notification System Activation** (November 2025)
- Email notifications fully configured with Gmail SMTP
- SMS notifications fully configured with Twilio API
- Professional RAAS branding in all notification messages
- All credentials stored securely as Replit Secrets
- Test script (test_notifications.py) for manual verification