#!/bin/bash

# PyTracking Production Deployment Script
# For Ubuntu/Debian servers

set -e

echo "🚀 PyTracking Production Deployment Script"
echo "=========================================="

# Configuration
DOMAIN=${1:-"realproductpat.com"}
APP_DIR="/var/www/pytracking"
DATA_DIR="/var/lib/pytracking"
LOG_DIR="/var/log/pytracking"
USER="pytracking"

echo "Deploying PyTracking for domain: $DOMAIN"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root (use sudo)"
   exit 1
fi

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install dependencies
echo "🔧 Installing system dependencies..."
apt install -y python3 python3-pip python3-venv nginx supervisor certbot python3-certbot-nginx curl

# Create application user
echo "👤 Creating application user..."
if ! id "$USER" &>/dev/null; then
    useradd -r -m -s /bin/bash $USER
fi

# Create directories
echo "📁 Creating directories..."
mkdir -p $APP_DIR $DATA_DIR $LOG_DIR
chown $USER:$USER $APP_DIR $DATA_DIR $LOG_DIR

# Setup Python environment
echo "🐍 Setting up Python environment..."
sudo -u $USER python3 -m venv $APP_DIR/venv
sudo -u $USER $APP_DIR/venv/bin/pip install --upgrade pip
sudo -u $USER $APP_DIR/venv/bin/pip install 'pytracking[all]' flask gunicorn jinja2 python-dotenv

# Copy application files (assumes they're in current directory)
if [ -f "production_server.py" ]; then
    echo "📋 Copying application files..."
    cp production_server.py $APP_DIR/
    cp requirements.txt $APP_DIR/
    [ -f "legal_correspondence.html" ] && cp legal_correspondence.html $APP_DIR/
    [ -f "generate_legal_email.py" ] && cp generate_legal_email.py $APP_DIR/
    chown -R $USER:$USER $APP_DIR
else
    echo "⚠️  Warning: production_server.py not found in current directory"
    echo "   Make sure to copy your application files to $APP_DIR manually"
fi

# Generate encryption key if not provided
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Create environment file
echo "⚙️  Creating environment configuration..."
cat > $APP_DIR/.env << EOF
PYTRACKING_ENCRYPTION_KEY=$ENCRYPTION_KEY
PYTRACKING_DB_PATH=$DATA_DIR/tracking.db
WEBHOOK_SECRET=$(openssl rand -hex 32)
ALLOWED_DOMAINS=$DOMAIN
FLASK_ENV=production
EOF

chown $USER:$USER $APP_DIR/.env
chmod 600 $APP_DIR/.env

# Create Nginx configuration
echo "🌐 Configuring Nginx..."
cat > /etc/nginx/sites-available/$DOMAIN << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;
    
    # SSL certificates (will be added by certbot)
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Logs
    access_log $LOG_DIR/nginx_access.log;
    error_log $LOG_DIR/nginx_error.log;
    
    # PyTracking application
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # For tracking pixels (no caching)
        location /track/ {
            proxy_pass http://127.0.0.1:5000;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            
            # Disable caching for tracking
            add_header Cache-Control "no-cache, no-store, must-revalidate";
            add_header Pragma "no-cache";
            add_header Expires "0";
        }
    }
    
    # Block access to sensitive files
    location ~ /\\. {
        deny all;
    }
    
    location ~ \\.(env|log)\$ {
        deny all;
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
nginx -t

# Create Supervisor configuration
echo "👮 Configuring Supervisor..."
cat > /etc/supervisor/conf.d/pytracking.conf << EOF
[program:pytracking]
command=$APP_DIR/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 production_server:app
directory=$APP_DIR
user=$USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=$LOG_DIR/gunicorn.log
environment=PATH="$APP_DIR/venv/bin"
EOF

# Initialize database
echo "🗄️  Initializing database..."
sudo -u $USER bash -c "cd $APP_DIR && source venv/bin/activate && python3 -c 'from production_server import init_db; init_db()'"

# Start services
echo "🔄 Starting services..."
systemctl restart nginx
supervisorctl reread
supervisorctl update
supervisorctl start pytracking

# Setup SSL certificate
echo "🔒 Setting up SSL certificate..."
echo "Follow the prompts to set up SSL certificate:"
certbot --nginx -d $DOMAIN -d www.$DOMAIN

# Create backup script
echo "💾 Creating backup script..."
cat > /usr/local/bin/pytracking-backup << EOF
#!/bin/bash
DATE=\$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/pytracking"
mkdir -p \$BACKUP_DIR
cp $DATA_DIR/tracking.db \$BACKUP_DIR/tracking_\$DATE.db
find \$BACKUP_DIR -name "tracking_*.db" -mtime +7 -delete
echo "Backup completed: tracking_\$DATE.db"
EOF

chmod +x /usr/local/bin/pytracking-backup

# Add to crontab
echo "⏰ Setting up daily backups..."
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/pytracking-backup >> /var/log/pytracking/backup.log 2>&1") | crontab -

# Create maintenance script
cat > /usr/local/bin/pytracking-status << EOF
#!/bin/bash
echo "PyTracking Service Status"
echo "========================"
echo "Nginx: \$(systemctl is-active nginx)"
echo "Supervisor: \$(systemctl is-active supervisor)"
echo "PyTracking: \$(supervisorctl status pytracking | awk '{print \$2}')"
echo ""
echo "Recent logs:"
echo "Gunicorn: \$(tail -2 $LOG_DIR/gunicorn.log)"
echo "Nginx: \$(tail -2 $LOG_DIR/nginx_access.log)"
echo ""
echo "Database size: \$(du -h $DATA_DIR/tracking.db | cut -f1)"
echo "Disk usage: \$(df -h $DATA_DIR | tail -1)"
EOF

chmod +x /usr/local/bin/pytracking-status

# Final checks
echo "✅ Running final checks..."
sleep 5

# Test application
if curl -s http://localhost:5000/health > /dev/null; then
    echo "✅ Application is running!"
else
    echo "❌ Application is not responding"
    echo "Check logs: supervisorctl tail pytracking"
fi

# Test Nginx
if nginx -t > /dev/null 2>&1; then
    echo "✅ Nginx configuration is valid!"
else
    echo "❌ Nginx configuration has errors"
fi

echo ""
echo "🎉 Deployment completed!"
echo "========================"
echo "Domain: https://$DOMAIN"
echo "Health check: https://$DOMAIN/health"
echo "Admin stats: https://$DOMAIN/admin/stats"
echo ""
echo "Useful commands:"
echo "  Status: pytracking-status"
echo "  Backup: pytracking-backup"
echo "  Logs: supervisorctl tail pytracking"
echo "  Restart: supervisorctl restart pytracking"
echo ""
echo "Environment variables saved to: $APP_DIR/.env"
echo "Encryption key: $ENCRYPTION_KEY"
echo ""
echo "⚠️  IMPORTANT: Save the encryption key securely!"
echo "   You'll need it for generating tracking URLs."
