#!/bin/bash
# Server troubleshooting commands
# Run these on your server to diagnose issues

echo "🔍 PyTracking Server Diagnostics"
echo "=================================="

echo "1. Checking application status..."
sudo supervisorctl status

echo ""
echo "2. Checking if application is listening on port 8000..."
netstat -tlnp | grep :8000 || ss -tlnp | grep :8000

echo ""
echo "3. Checking nginx status..."
sudo systemctl status nginx --no-pager

echo ""
echo "4. Checking nginx configuration..."
sudo nginx -t

echo ""
echo "5. Checking what's listening on port 80 and 443..."
netstat -tlnp | grep :80 || ss -tlnp | grep :80
netstat -tlnp | grep :443 || ss -tlnp | grep :443

echo ""
echo "6. Testing local connection to Flask app..."
curl -s http://localhost:8000/health || echo "Flask app not responding on localhost:8000"

echo ""
echo "7. Testing nginx proxy..."
curl -s http://localhost/health || echo "Nginx proxy not working"

echo ""
echo "8. Checking application logs..."
echo "Recent supervisor logs:"
sudo tail -5 /var/log/supervisor/pytracking.log

echo ""
echo "9. Checking if pytracking directory exists and has files..."
ls -la /home/pytracking/pytracking/

echo ""
echo "10. Checking DNS resolution..."
nslookup realproductpat.com

echo ""
echo "🔧 Quick fixes to try:"
echo "- If Flask app not running: cd /home/pytracking/pytracking && source venv/bin/activate && python app.py"
echo "- If nginx issues: sudo systemctl restart nginx"
echo "- If SSL issues: try http://realproductpat.com/health first"
