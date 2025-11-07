# RAAS Deployment Guide

This guide covers three deployment options for RAAS (Reminder as a Service).

---

## 🚀 Option 1: Replit Publishing (Recommended for Quick Deployment)

**Easiest option** - Deploy directly from Replit with one click.

### Steps:

1. **Click the "Deploy" button** in your Replit workspace
2. **Choose deployment type**:
   - **Autoscale**: Recommended for RAAS (handles variable traffic)
   - Machine size: Start with 0.5 vCPU / 1GB RAM
3. **Configure environment variables**:
   - Add all secrets from your Replit Secrets to the deployment
   - `SENDER_EMAIL`, `SENDER_PASSWORD`, `TWILIO_ACCOUNT_SID`, etc.
4. **Deploy**: Click "Deploy" and wait for the build to complete

### Benefits:
- ✅ Automatic HTTPS/SSL
- ✅ Custom domain support
- ✅ Automatic scaling
- ✅ Built-in monitoring and logs
- ✅ Zero infrastructure management

### Cost:
- Starts at $7/month for Reserved VM
- Autoscale: Pay only for actual usage

---

## 🐳 Option 2: Docker Deployment (Any Cloud Provider)

Deploy containerized RAAS to AWS, Azure, DigitalOcean, or any cloud with Docker support.

### Prerequisites:
- Docker and Docker Compose installed
- Cloud server (EC2, Droplet, etc.)
- Domain name (optional)

### Local Testing:

```bash
# 1. Copy environment variables
cp .env.example .env

# 2. Edit .env with your credentials
nano .env

# 3. Build and run containers
docker-compose up -d

# 4. Access the app
# Streamlit: http://localhost:5000
# API: http://localhost:8000/docs
```

### Cloud Deployment:

#### **AWS EC2 / DigitalOcean Droplet:**

```bash
# SSH into your server
ssh user@your-server-ip

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Clone your repository
git clone https://github.com/yourusername/raas.git
cd raas

# Set up environment variables
nano .env  # Add your secrets

# Start the application
docker-compose up -d

# View logs
docker-compose logs -f
```

#### **Set up NGINX reverse proxy** (for production):

```nginx
# /etc/nginx/sites-available/raas
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Enable site and reload NGINX
sudo ln -s /etc/nginx/sites-available/raas /etc/nginx/sites-enabled/
sudo systemctl reload nginx

# Install SSL with Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## 🔄 Option 3: GitHub Actions CI/CD

Automatically build, test, and deploy when you push to GitHub.

### Setup:

1. **Push code to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/raas.git
   git push -u origin main
   ```

2. **Add GitHub Secrets** (Settings → Secrets and variables → Actions):
   - `DOCKERHUB_USERNAME` - Your Docker Hub username
   - `DOCKERHUB_TOKEN` - Docker Hub access token
   - `SSH_HOST` - Server IP address
   - `SSH_USERNAME` - SSH user (e.g., ubuntu)
   - `SSH_PRIVATE_KEY` - Private SSH key content
   - `SSH_PORT` - SSH port (default: 22)

3. **Workflow automatically runs on push to main**:
   - Lints code
   - Tests Docker builds
   - Builds and pushes images to Docker Hub
   - SSH into server and deploys

### Manual Deployment Trigger:
Go to **Actions** → **CD Pipeline** → **Run workflow**

---

## 📊 Monitoring & Maintenance

### Docker Commands:

```bash
# View running containers
docker-compose ps

# View logs
docker-compose logs -f raas-app
docker-compose logs -f raas-api

# Restart services
docker-compose restart

# Update to latest version
git pull
docker-compose pull
docker-compose up -d --force-recreate

# Backup database
docker-compose exec raas-app tar -czf /app/backup.tar.gz /app/data
docker cp raas-app:/app/backup.tar.gz ./backup.tar.gz
```

### Health Checks:

```bash
# Check API health
curl http://your-domain.com/api/

# Check Streamlit health
curl http://your-domain.com/_stcore/health
```

---

## 🌐 Cloud Provider Options

### **AWS (Elastic Beanstalk)**:
Upload `docker-compose.yml` directly to Elastic Beanstalk

### **Azure (Container Instances)**:
```bash
az container create --resource-group raas-rg \
  --name raas --image yourusername/raas-app:latest
```

### **Google Cloud Run**:
```bash
gcloud run deploy raas-app --image yourusername/raas-app:latest \
  --platform managed --region us-central1 --allow-unauthenticated
```

### **DigitalOcean App Platform**:
1. Create new app from Docker Hub
2. Connect your Docker images
3. Add environment variables
4. Deploy

---

## 🔐 Security Checklist

- ✅ Use environment variables for all secrets
- ✅ Enable HTTPS/SSL (automatic on Replit, use Let's Encrypt elsewhere)
- ✅ Run containers as non-root user (already configured)
- ✅ Keep Docker images updated
- ✅ Use strong passwords for database and admin access
- ✅ Set up firewall rules (allow only 80, 443, 22)
- ✅ Regular backups of database

---

## 💰 Cost Comparison

| Provider | Monthly Cost | Best For |
|----------|-------------|----------|
| **Replit Autoscale** | ~$7-20 | Quick deployment, automatic scaling |
| **DigitalOcean Droplet** | $6-12 | Full control, predictable costs |
| **AWS EC2 (t3.micro)** | ~$8 | AWS ecosystem integration |
| **Azure App Service** | ~$10 | Microsoft ecosystem |
| **Google Cloud Run** | Pay-per-use | Sporadic traffic, low usage |

---

## 🚦 Quick Start Recommendations

**For rapid deployment**: Use **Replit Publishing** (Option 1)

**For full control**: Use **Docker on DigitalOcean** (Option 2)

**For professional CI/CD**: Use **GitHub Actions** (Option 3)

---

## 📞 Support

For issues or questions:
- Check logs: `docker-compose logs -f`
- Verify environment variables: `docker-compose config`
- Test connectivity: `curl http://localhost:5000/_stcore/health`
