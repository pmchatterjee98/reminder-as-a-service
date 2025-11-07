# ⚡ RAAS — Reminder as a Service

**Never miss what matters**

A comprehensive task management application with automated email, SMS, and WhatsApp reminders. Built with Streamlit and FastAPI, featuring a modern dark-themed UI and complete REST API.

---

## ✨ Features

- 📋 **Smart Task Management**: Create tasks with titles, descriptions, due dates, and contact information
- 🔔 **Multi-Channel Reminders**: Email, SMS, and WhatsApp notifications with customizable intervals (1 hour to 7 days)
- 🔁 **Recurring Tasks**: Automatic rescheduling for daily, weekly, monthly, and yearly tasks
- 🎯 **Organization**: Categories and priority levels (High/Medium/Low) with color-coded indicators
- 🔍 **Advanced Filtering**: Filter by category, priority, and completion status
- 📥 **Export Options**: Export to CSV or PDF with timestamped filenames
- 🎨 **Modern UI**: Dark-themed interface with custom RAAS branding
- 🚀 **REST API**: Full FastAPI backend with automatic Swagger documentation
- 📱 **Mobile Optimized**: Full iPhone/iPad support with PWA installability

---

## 🚀 Quick Start

### Local Development

```bash
# Clone the repository
git clone https://github.com/yourusername/raas.git
cd raas

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials

# Run Streamlit app
streamlit run app.py --server.port 5000

# Run API (in another terminal)
uvicorn api:app --host 0.0.0.0 --port 8000
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Access the app
# Streamlit UI: http://localhost:5000
# API Documentation: http://localhost:8000/docs
```

---

## 📦 Deployment Options

### Option 1: Replit Publishing (Easiest)
1. Click "Deploy" in your Replit workspace
2. Choose Autoscale deployment
3. Add environment variables
4. Deploy with one click

[See detailed deployment guide →](DEPLOYMENT.md)

### Option 2: Docker (Any Cloud)
Deploy to AWS, Azure, DigitalOcean, or any cloud with Docker support.

[See Docker deployment guide →](DEPLOYMENT.md#option-2-docker-deployment-any-cloud-provider)

### Option 3: GitHub Actions CI/CD
Automated testing and deployment on every push.

[See CI/CD setup guide →](DEPLOYMENT.md#option-3-github-actions-cicd)

---

## 🔧 Configuration

### Required Environment Variables

```bash
# Email Configuration (Gmail)
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password

# Twilio Configuration (SMS & WhatsApp)
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890
```

### WhatsApp Setup

To enable WhatsApp notifications:
1. Log into your Twilio Console
2. Navigate to WhatsApp Sandbox
3. Send "join <your-sandbox-code>" to whatsapp:+14155238886
4. Add WhatsApp phone numbers to your reminders

---

## 🏗️ Architecture

```
raas/
├── app.py              # Streamlit frontend application
├── api.py              # FastAPI REST API
├── database.py         # SQLite database operations
├── scheduler.py        # Background reminder scheduler
├── notifications.py    # Email, SMS, and WhatsApp delivery
├── docker-compose.yml  # Multi-container orchestration
└── .github/workflows/  # CI/CD pipelines
    ├── ci.yml         # Continuous Integration
    └── cd.yml         # Continuous Deployment
```

---

## 🌐 API Endpoints

Full REST API with automatic documentation:

- `GET /` - API information
- `GET /todos` - List all todos (with filtering)
- `GET /todos/{id}` - Get specific todo
- `POST /todos` - Create new todo
- `PUT /todos/{id}` - Update todo
- `DELETE /todos/{id}` - Delete todo
- `POST /todos/{id}/toggle-complete` - Toggle completion
- `GET /stats` - Get statistics

**Interactive API Docs**: http://localhost:8000/docs

---

## 📱 Use on iPhone

RAAS is fully optimized for mobile! Install it on your iPhone home screen:

1. Open your published RAAS URL in **Safari** on iPhone
2. Tap the **Share button** (square with arrow)
3. Select **"Add to Home Screen"**
4. Tap **"Add"**

Now RAAS opens fullscreen like a native app! See [MOBILE_GUIDE.md](MOBILE_GUIDE.md) for full details.

### Mobile Features:
- ✅ Touch-optimized buttons (44px iOS standard)
- ✅ Responsive layout for all iPhone sizes
- ✅ No zoom on form inputs
- ✅ Fullscreen app experience
- ✅ Progressive Web App (PWA) support
- ✅ Works offline for viewing reminders

---

## 🎨 UI Preview

- Modern dark theme with RAAS color palette
- Priority badges (High/Medium/Low)
- Days remaining indicators
- Clean list view with action buttons
- Fully responsive design (desktop + mobile)

---

## 🔐 Security

- Non-root Docker containers
- Environment-based secret management
- HTTPS/SSL support (automatic on Replit)
- Input validation with Pydantic
- Secure password handling for email

---

## 📊 Tech Stack

**Frontend**:
- Streamlit - Interactive web UI
- Custom CSS - Dark theme styling

**Backend**:
- FastAPI - REST API framework
- Pydantic - Data validation
- Uvicorn - ASGI server

**Database**:
- SQLite - Local persistence
- Automatic schema migrations

**Notifications**:
- Gmail SMTP - Email delivery
- Twilio - SMS and WhatsApp

**Scheduling**:
- APScheduler - Background job processing

**Deployment**:
- Docker - Containerization
- Docker Compose - Multi-service orchestration
- GitHub Actions - CI/CD automation

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📝 License

This project is open source and available under the MIT License.

---

## 🙏 Acknowledgments

Built with modern Python tools and best practices for a production-ready reminder service.

**Made with ❤️ using Replit**
