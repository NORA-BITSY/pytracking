#!/bin/bash
# Quick server fixes for PyTracking
# Run as root on your server

echo "🔧 Fixing PyTracking Server Issues"
echo "=================================="

# 1. First, let's make sure the Flask app is running properly
echo "1. Checking Flask application..."
cd /home/pytracking/pytracking

# Check if app.py exists
if [ ! -f "app.py" ]; then
    echo "❌ app.py not found! You need to upload your files first."
    echo "Run this from your local machine:"
    echo "  scp app.py root@143.110.214.80:/home/pytracking/pytracking/"
    exit 1
fi

# 2. Install missing packages if needed
echo "2. Installing/updating packages..."
su - pytracking -c "cd /home/pytracking/pytracking && python3 -m venv venv && source venv/bin/activate && pip install flask gunicorn psycopg2-binary python-dotenv 'pytracking[all]'"

# 3. Create a simple systemd service instead of supervisor
echo "3. Creating systemd service..."
cat > /etc/systemd/system/pytracking.service << 'EOF'
[Unit]
Description=PyTracking Flask Application
After=network.target

[Service]
Type=simple
User=pytracking
WorkingDirectory=/home/pytracking/pytracking
Environment=PATH=/home/pytracking/pytracking/venv/bin
ExecStart=/home/pytracking/pytracking/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 4. Enable and start the service
systemctl daemon-reload
systemctl enable pytracking
systemctl start pytracking

# 5. Configure nginx properly
echo "4. Configuring nginx..."
cat > /etc/nginx/sites-available/realproductpat.com << 'EOF'
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

    location /track/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Remove default nginx site
rm -f /etc/nginx/sites-enabled/default

# Enable our site
ln -sf /etc/nginx/sites-available/realproductpat.com /etc/nginx/sites-enabled/

# Test and reload nginx
nginx -t && systemctl reload nginx

# 6. Check services
echo "5. Checking service status..."
systemctl status pytracking --no-pager
systemctl status nginx --no-pager

# 7. Test the setup
echo "6. Testing setup..."
sleep 2
curl -s http://localhost:8000/health && echo "✅ Flask app working"
curl -s http://localhost/health && echo "✅ Nginx proxy working"

echo ""
echo "🎯 Setup complete! Try these tests:"
echo "From your server:"
echo "  curl http://localhost/health"
echo "  curl http://143.110.214.80/health"
echo ""
echo "From your local machine:"
echo "  curl http://143.110.214.80/health"
echo ""
echo "If working, then configure DNS and SSL:"
echo "  1. Point realproductpat.com DNS to 143.110.214.80"
echo "  2. Run: certbot --nginx -d realproductpat.com"
