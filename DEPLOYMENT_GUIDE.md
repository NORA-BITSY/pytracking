# PyTracking Server Deployment Guide

## 🚀 Deployment Options for realproductpat.com

### Option 1: Simple VPS/Server Deployment (Recommended)

#### Step 1: Server Setup

1. **Get a server** (VPS, DigitalOcean, Linode, AWS EC2, etc.)
   - Minimum: 1GB RAM, 1 CPU core
   - OS: Ubuntu 20.04+ or CentOS 8+

2. **Install dependencies:**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.8+
sudo apt install python3 python3-pip python3-venv nginx supervisor -y

# Install certbot for SSL
sudo apt install certbot python3-certbot-nginx -y
```

#### Step 2: Application Setup

1. **Create application directory:**
```bash
sudo mkdir -p /var/www/pytracking
sudo chown $USER:$USER /var/www/pytracking
cd /var/www/pytracking
```

2. **Copy your application:**
```bash
# Option A: Copy files from your local machine
scp -r /Users/productpat/Library/CloudStorage/Dropbox/pytracking/* user@your-server:/var/www/pytracking/

# Option B: Clone from Git (if you've pushed to a repo)
git clone https://github.com/yourusername/pytracking.git .
```

3. **Set up Python environment:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install 'pytracking[all]' flask gunicorn jinja2
```

4. **Set environment variables:**
```bash
# Create .env file
cat > .env << EOF
PYTRACKING_ENCRYPTION_KEY=ioarP4JdASrV8qMBoQz2MtTJrk7Qy4cyZTArJg9sWs8=
PYTRACKING_DB_PATH=/var/lib/pytracking/tracking.db
WEBHOOK_SECRET=your-super-secret-webhook-key-change-this
ALLOWED_DOMAINS=realproductpat.com
EOF

# Create database directory
sudo mkdir -p /var/lib/pytracking
sudo chown $USER:$USER /var/lib/pytracking

# Create log directory
sudo mkdir -p /var/log/pytracking
sudo chown $USER:$USER /var/log/pytracking
```

#### Step 3: Nginx Configuration

Create `/etc/nginx/sites-available/realproductpat.com`:

```nginx
server {
    listen 80;
    server_name realproductpat.com www.realproductpat.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name realproductpat.com www.realproductpat.com;
    
    # SSL certificates (will be added by certbot)
    # ssl_certificate /etc/letsencrypt/live/realproductpat.com/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/realproductpat.com/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # PyTracking application
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # For tracking pixels (no caching)
        location /track/ {
            proxy_pass http://127.0.0.1:5000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Disable caching for tracking
            add_header Cache-Control "no-cache, no-store, must-revalidate";
            add_header Pragma "no-cache";
            add_header Expires "0";
        }
    }
    
    # Static files (if any)
    location /static/ {
        alias /var/www/pytracking/static/;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
    
    # Block access to sensitive files
    location ~ /\. {
        deny all;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/realproductpat.com /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Step 4: SSL Certificate

```bash
# Get SSL certificate
sudo certbot --nginx -d realproductpat.com -d www.realproductpat.com

# Test auto-renewal
sudo certbot renew --dry-run
```

#### Step 5: Process Management with Supervisor

Create `/etc/supervisor/conf.d/pytracking.conf`:

```ini
[program:pytracking]
command=/var/www/pytracking/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 production_server:app
directory=/var/www/pytracking
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/pytracking/gunicorn.log
environment=PATH="/var/www/pytracking/venv/bin",PYTRACKING_ENCRYPTION_KEY="ioarP4JdASrV8qMBoQz2MtTJrk7Qy4cyZTArJg9sWs8=",PYTRACKING_DB_PATH="/var/lib/pytracking/tracking.db"
```

Start the service:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start pytracking
sudo supervisorctl status
```

---

### Option 2: Docker Deployment

#### Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for data
RUN mkdir -p /app/data /app/logs

# Set environment variables
ENV PYTRACKING_DB_PATH=/app/data/tracking.db
ENV FLASK_APP=production_server.py

# Expose port
EXPOSE 5000

# Run application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "production_server:app"]
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  pytracking:
    build: .
    ports:
      - "5000:5000"
    environment:
      - PYTRACKING_ENCRYPTION_KEY=ioarP4JdASrV8qMBoQz2MtTJrk7Qy4cyZTArJg9sWs8=
      - PYTRACKING_DB_PATH=/app/data/tracking.db
      - WEBHOOK_SECRET=your-webhook-secret
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
    depends_on:
      - pytracking
    restart: unless-stopped
```

Deploy with:
```bash
docker-compose up -d
```

---

### Option 3: Cloud Platform Deployment

#### A. Heroku

1. **Create requirements.txt:**
```txt
pytracking[all]==0.2.3
flask==2.3.3
gunicorn==21.2.0
jinja2==3.1.2
```

2. **Create Procfile:**
```
web: gunicorn production_server:app
```

3. **Deploy:**
```bash
heroku create realproductpat-tracking
heroku config:set PYTRACKING_ENCRYPTION_KEY=ioarP4JdASrV8qMBoQz2MtTJrk7Qy4cyZTArJg9sWs8=
heroku config:set PYTRACKING_DB_PATH=/app/tracking.db
git push heroku main
```

#### B. AWS Lambda + API Gateway

Use Zappa for serverless deployment:

```bash
pip install zappa
zappa init
zappa deploy production
```

---

## 🔧 Configuration for Your Domain

Update these URLs in your code to match your actual server:

```python
# In your tracking configuration
config = pytracking.Configuration(
    base_open_tracking_url="https://realproductpat.com/track/open/",
    base_click_tracking_url="https://realproductpat.com/track/click/",
    webhook_url="https://realproductpat.com/webhooks/tracking/",
    encryption_bytestring_key=ENCRYPTION_KEY
)
```

## 📊 Testing Your Deployment

1. **Health check:**
```bash
curl https://realproductpat.com/health
```

2. **Create a test email:**
```bash
cd /var/www/pytracking
source venv/bin/activate
python generate_legal_email.py
```

3. **Check tracking stats:**
```
https://realproductpat.com/admin/stats
```

## 🔒 Security Considerations

1. **Firewall:** Only allow ports 22 (SSH), 80 (HTTP), 443 (HTTPS)
2. **Database:** Use strong encryption key, store securely
3. **Admin endpoints:** Add authentication for `/admin/stats`
4. **Logs:** Monitor `/var/log/pytracking/` for suspicious activity
5. **Backups:** Regular database backups
6. **SSL:** Keep certificates updated

## 📈 Monitoring & Maintenance

1. **Log monitoring:**
```bash
tail -f /var/log/pytracking/gunicorn.log
tail -f /var/log/nginx/access.log
```

2. **Database backup:**
```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cp /var/lib/pytracking/tracking.db /var/backups/tracking_$DATE.db
find /var/backups -name "tracking_*.db" -mtime +7 -delete
```

3. **System monitoring:**
- CPU/Memory usage
- Disk space
- SSL certificate expiry
- Application errors

## 🎯 You Don't Need to Host the Repository

**Key Point:** You don't need to host the entire repository on your server. You only need:

1. `production_server.py` (the Flask app)
2. `pytracking` package (installed via pip)
3. Your generated emails
4. Configuration files

The PyTracking library itself is installed via pip, so you just need your application code on the server.

## 🔄 Workflow Summary

1. **Develop locally:** Create emails, test tracking
2. **Deploy server:** Copy application files, not the whole repo
3. **Generate emails:** Run scripts to create tracked emails
4. **Send emails:** Use your email service (SMTP, SendGrid, etc.)
5. **Monitor:** Check stats and logs on your server

Would you like me to help you set up any specific deployment option?
