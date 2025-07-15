# PyTracking Server Deployment Guide

## Server Information
- **Server IP**: 143.110.214.80
- **Domain**: realproductpat.com
- **Purpose**: Email tracking with open tracking, webhooks, and database

## 🚀 Quick Deployment Steps

### 1. Prepare Your Server

```bash
# SSH into your server
ssh root@143.110.214.80

# Update system
apt update && apt upgrade -y

# Install required packages
apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib supervisor git

# Create application user
useradd -m -s /bin/bash pytracking
usermod -aG sudo pytracking
```

### 2. Deploy PyTracking Application

```bash
# Switch to application user
su - pytracking

# Clone your repository (or upload files)
git clone https://github.com/NORA-BITSY/pytracking.git
cd pytracking

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install 'pytracking[all]'
pip install flask gunicorn psycopg2-binary python-dotenv

# Copy your local files to server
# (You'll need to scp these from your local machine)
```

### 3. Database Setup

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE pytracking_db;
CREATE USER pytracking_user WITH PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE pytracking_db TO pytracking_user;
\q
```

### 4. Environment Configuration

Create `/home/pytracking/pytracking/.env`:
```env
FLASK_ENV=production
SECRET_KEY=your_super_secret_key_here
DATABASE_URL=postgresql://pytracking_user:your_secure_password_here@localhost/pytracking_db
TRACKING_ENCRYPTION_KEY=ioarP4JdASrV8qMBoQz2MtTJrk7Qy4cyZTArJg9sWs8=
DOMAIN=realproductpat.com
```

### 5. Nginx Configuration

Create `/etc/nginx/sites-available/realproductpat.com`:
```nginx
server {
    listen 80;
    server_name realproductpat.com www.realproductpat.com 143.110.214.80;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Specific handling for tracking endpoints
    location /track/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Log tracking requests
        access_log /var/log/nginx/tracking.log;
    }

    # Webhook endpoints
    location /webhooks/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/realproductpat.com /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. SSL Setup (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d realproductpat.com -d www.realproductpat.com
```

## 📁 File Transfer Commands

Run these from your local machine to upload files to server:

```bash
# Transfer the entire pytracking directory
scp -r /Users/productpat/Library/CloudStorage/Dropbox/pytracking/ root@143.110.214.80:/home/pytracking/

# Or transfer specific files
scp /Users/productpat/Library/CloudStorage/Dropbox/pytracking/legal_correspondence_tracked.html root@143.110.214.80:/home/pytracking/pytracking/
scp /Users/productpat/Library/CloudStorage/Dropbox/pytracking/legal_tracking_info.txt root@143.110.214.80:/home/pytracking/pytracking/
scp /Users/productpat/Library/CloudStorage/Dropbox/pytracking/email_*.html root@143.110.214.80:/home/pytracking/pytracking/

# Set correct ownership
ssh root@143.110.214.80 "chown -R pytracking:pytracking /home/pytracking/"
```

## 🔄 Process Management

The system will run continuously using these commands:

```bash
# Start the Flask application
cd /home/pytracking/pytracking
source venv/bin/activate
gunicorn -w 4 -b 127.0.0.1:8000 app:app

# Or use supervisor for automatic restart
sudo systemctl enable supervisor
sudo systemctl start supervisor
```

## 📊 Monitoring & Logs

```bash
# View tracking logs
tail -f /var/log/nginx/tracking.log

# View application logs
tail -f /home/pytracking/pytracking/app.log

# Database queries
sudo -u postgres psql pytracking_db -c "SELECT * FROM tracking_events ORDER BY created_at DESC LIMIT 10;"
```
