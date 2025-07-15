#!/bin/bash
# Upload PyTracking files to your server
# Run this from your local machine

SERVER_IP="143.110.214.80"
SERVER_USER="root"
APP_DIR="/home/pytracking/pytracking"

echo "🚀 Uploading PyTracking files to server $SERVER_IP"

# Make sure the app directory exists
ssh $SERVER_USER@$SERVER_IP "mkdir -p $APP_DIR"

echo "📁 Uploading application files..."

# Upload main application files
scp app.py $SERVER_USER@$SERVER_IP:$APP_DIR/
scp requirements_server.txt $SERVER_USER@$SERVER_IP:$APP_DIR/
scp pytracking.conf $SERVER_USER@$SERVER_IP:$APP_DIR/

# Upload your generated emails
echo "📧 Uploading email files..."
scp legal_correspondence_tracked.html $SERVER_USER@$SERVER_IP:$APP_DIR/
scp legal_tracking_info.txt $SERVER_USER@$SERVER_IP:$APP_DIR/
scp email_*.html $SERVER_USER@$SERVER_IP:$APP_DIR/ 2>/dev/null || echo "No email_*.html files found"

# Upload scripts
echo "🔧 Uploading utility scripts..."
scp generate_legal_email.py $SERVER_USER@$SERVER_IP:$APP_DIR/
scp verify_installation.py $SERVER_USER@$SERVER_IP:$APP_DIR/

# Upload documentation
echo "📚 Uploading documentation..."
scp *.md $SERVER_USER@$SERVER_IP:$APP_DIR/

# Set correct ownership
echo "🔒 Setting file permissions..."
ssh $SERVER_USER@$SERVER_IP "chown -R pytracking:pytracking $APP_DIR"

echo "✅ Upload complete!"
echo ""
echo "🔄 Next steps on server:"
echo "1. SSH to server: ssh $SERVER_USER@$SERVER_IP"
echo "2. Switch to app user: su - pytracking"
echo "3. Go to app directory: cd pytracking"
echo "4. Restart application: sudo supervisorctl restart pytracking"
echo ""
echo "🌐 Your tracking system will be available at:"
echo "   https://realproductpat.com"
echo "   https://realproductpat.com/health (to test)"
echo "   https://realproductpat.com/admin/events (to view tracking)"
