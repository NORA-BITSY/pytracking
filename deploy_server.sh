#!/bin/bash
# Complete PyTracking Server Deployment Script
# Run this script on your server at 143.110.214.80

set -e  # Exit on any error

echo "🚀 Starting PyTracking deployment on realproductpat.com"
echo "Server IP: 143.110.214.80"
echo "Timestamp: $(date)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_warning "Running as root. Will create pytracking user."
else
   print_error "Please run this script as root (sudo)"
   exit 1
fi

print_status "Step 1: System Update and Package Installation"
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib supervisor git curl

print_status "Step 2: Create Application User"
if id "pytracking" &>/dev/null; then
    print_warning "User pytracking already exists"
else
    useradd -m -s /bin/bash pytracking
    usermod -aG sudo pytracking
    print_status "Created user: pytracking"
fi

print_status "Step 3: Database Setup"
sudo -u postgres psql -c "CREATE DATABASE pytracking_db;" 2>/dev/null || print_warning "Database pytracking_db may already exist"
sudo -u postgres psql -c "CREATE USER pytracking_user WITH PASSWORD 'PyTrack2025!SecurePass';" 2>/dev/null || print_warning "User pytracking_user may already exist"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE pytracking_db TO pytracking_user;"
print_status "Database setup completed"

print_status "Step 4: Application Directory Setup"
cd /home/pytracking

# Create directory structure
sudo -u pytracking mkdir -p pytracking
cd pytracking

print_status "Step 5: Python Environment Setup"
sudo -u pytracking python3 -m venv venv
sudo -u pytracking bash -c "source venv/bin/activate && pip install --upgrade pip"

# Create requirements file
cat > requirements_server.txt << 'EOF'
pytracking[all]
Flask==2.3.3
gunicorn==21.2.0
psycopg2-binary==2.9.7
python-dotenv==1.0.0
requests==2.31.0
cryptography>=41.0.0
EOF

sudo -u pytracking bash -c "source venv/bin/activate && pip install -r requirements_server.txt"
print_status "Python packages installed"

print_status "Step 6: Environment Configuration"
cat > .env << 'EOF'
FLASK_ENV=production
SECRET_KEY=PyTrack2025SuperSecretKeyChangeThis!
DATABASE_URL=postgresql://pytracking_user:PyTrack2025!SecurePass@localhost/pytracking_db
TRACKING_ENCRYPTION_KEY=ioarP4JdASrV8qMBoQz2MtTJrk7Qy4cyZTArJg9sWs8=
DOMAIN=realproductpat.com
EOF

chown pytracking:pytracking .env
print_status "Environment configuration created"

print_status "Step 7: Nginx Configuration"
cat > /etc/nginx/sites-available/realproductpat.com << 'EOF'
server {
    listen 80;
    server_name realproductpat.com www.realproductpat.com 143.110.214.80;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Specific handling for tracking endpoints
    location /track/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Log tracking requests
        access_log /var/log/nginx/tracking.log combined;
        
        # Fast response for tracking pixels
        proxy_connect_timeout 5s;
        proxy_send_timeout 5s;
        proxy_read_timeout 5s;
    }

    # Webhook endpoints
    location /webhooks/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Larger body size for webhook payloads
        client_max_body_size 10M;
    }
    
    # Admin endpoints (you may want to restrict access)
    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Optional: Restrict admin access
        # allow 143.110.214.80;
        # deny all;
    }
}
EOF

# Remove default nginx site if it exists
rm -f /etc/nginx/sites-enabled/default

# Enable our site
ln -sf /etc/nginx/sites-available/realproductpat.com /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
print_status "Nginx configured and reloaded"

print_status "Step 8: Supervisor Configuration"
cat > /etc/supervisor/conf.d/pytracking.conf << 'EOF'
[program:pytracking]
command=/home/pytracking/pytracking/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 app:app --timeout 30 --keep-alive 5
directory=/home/pytracking/pytracking
user=pytracking
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
killasgroup=true
priority=998
environment=PATH="/home/pytracking/pytracking/venv/bin"
stdout_logfile=/var/log/supervisor/pytracking.log
stderr_logfile=/var/log/supervisor/pytracking_error.log
EOF

print_status "Step 9: SSL Certificate Setup (Let's Encrypt)"
apt install -y certbot python3-certbot-nginx
print_warning "Setting up SSL certificate for realproductpat.com"

# Try to get SSL certificate
if certbot --nginx -d realproductpat.com -d www.realproductpat.com --non-interactive --agree-tos --email admin@realproductpat.com; then
    print_status "SSL certificate obtained successfully"
else
    print_warning "SSL certificate setup failed. You may need to configure DNS first."
    print_warning "Run this command later: certbot --nginx -d realproductpat.com -d www.realproductpat.com"
fi

print_status "Step 10: File Ownership and Permissions"
chown -R pytracking:pytracking /home/pytracking/
chmod 644 /home/pytracking/pytracking/.env

print_status "Step 11: Service Management"
systemctl enable supervisor
systemctl restart supervisor
supervisorctl reread
supervisorctl update

print_status "Step 12: Firewall Configuration"
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable

print_status "🎉 Deployment completed successfully!"
echo ""
echo "=================================================="
echo "📋 DEPLOYMENT SUMMARY"
echo "=================================================="
echo "🌐 Domain: https://realproductpat.com"
echo "🖥️  Server IP: 143.110.214.80"
echo "📁 App Directory: /home/pytracking/pytracking/"
echo "🔧 User: pytracking"
echo ""
echo "📡 ENDPOINTS:"
echo "  - Home: https://realproductpat.com/"
echo "  - Health: https://realproductpat.com/health"
echo "  - Admin: https://realproductpat.com/admin/events"
echo "  - Tracking: https://realproductpat.com/track/open/<data>"
echo "  - Webhooks: https://realproductpat.com/webhooks/tracking/"
echo ""
echo "📊 MONITORING:"
echo "  - App logs: tail -f /var/log/supervisor/pytracking.log"
echo "  - Tracking logs: tail -f /var/log/nginx/tracking.log"
echo "  - Service status: supervisorctl status pytracking"
echo ""
echo "🔄 MANAGEMENT COMMANDS:"
echo "  - Restart app: supervisorctl restart pytracking"
echo "  - View status: supervisorctl status"
echo "  - Database: sudo -u postgres psql pytracking_db"
echo ""
echo "⚠️  NEXT STEPS:"
echo "1. Upload your application files (app.py, emails, etc.)"
echo "2. Test the endpoints"
echo "3. Configure DNS to point realproductpat.com to 143.110.214.80"
echo "4. Send your tracked emails!"
echo ""
print_status "Ready to serve PyTracking on realproductpat.com! 🚀"
