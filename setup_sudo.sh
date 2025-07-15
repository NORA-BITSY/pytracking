#!/bin/bash
# Configure sudo permissions for pytracking user
# Run as root on your server

echo "🔐 Configuring sudo permissions for pytracking user"
echo "=================================================="

# Check if pytracking user exists
if id "pytracking" &>/dev/null; then
    echo "✅ User 'pytracking' exists"
else
    echo "❌ User 'pytracking' does not exist. Creating user..."
    useradd -m -s /bin/bash pytracking
    echo "✅ User 'pytracking' created"
fi

# Add pytracking user to sudo group
echo "1. Adding pytracking to sudo group..."
usermod -aG sudo pytracking

# Verify the user is in sudo group
echo "2. Verifying group membership..."
groups pytracking

# Create a specific sudoers file for pytracking (more secure)
echo "3. Creating sudoers configuration..."
cat > /etc/sudoers.d/pytracking << 'EOF'
# Allow pytracking user to run specific commands without password
pytracking ALL=(ALL) NOPASSWD: /bin/systemctl restart pytracking
pytracking ALL=(ALL) NOPASSWD: /bin/systemctl start pytracking
pytracking ALL=(ALL) NOPASSWD: /bin/systemctl stop pytracking
pytracking ALL=(ALL) NOPASSWD: /bin/systemctl status pytracking
pytracking ALL=(ALL) NOPASSWD: /bin/systemctl reload nginx
pytracking ALL=(ALL) NOPASSWD: /bin/systemctl restart nginx
pytracking ALL=(ALL) NOPASSWD: /usr/bin/supervisorctl restart pytracking
pytracking ALL=(ALL) NOPASSWD: /usr/bin/supervisorctl status pytracking
pytracking ALL=(ALL) NOPASSWD: /usr/bin/supervisorctl start pytracking
pytracking ALL=(ALL) NOPASSWD: /usr/bin/supervisorctl stop pytracking
pytracking ALL=(ALL) NOPASSWD: /usr/sbin/nginx -t
pytracking ALL=(ALL) NOPASSWD: /bin/chown -R pytracking\:pytracking /home/pytracking/*
pytracking ALL=(ALL) NOPASSWD: /bin/chmod +x /home/pytracking/pytracking/*

# Allow full sudo access with password for other commands
pytracking ALL=(ALL:ALL) ALL
EOF

# Set correct permissions on sudoers file
chmod 440 /etc/sudoers.d/pytracking

# Validate sudoers configuration
echo "4. Validating sudoers configuration..."
if visudo -c; then
    echo "✅ Sudoers configuration is valid"
else
    echo "❌ Sudoers configuration has errors - removing file"
    rm -f /etc/sudoers.d/pytracking
    exit 1
fi

# Test sudo access
echo "5. Testing sudo access for pytracking user..."
su - pytracking -c "sudo -l" 2>/dev/null && echo "✅ Sudo access working" || echo "❌ Sudo access not working"

# Set up home directory permissions
echo "6. Setting up home directory permissions..."
chown -R pytracking:pytracking /home/pytracking/
chmod 755 /home/pytracking/

# Create .bashrc with useful aliases for pytracking user
echo "7. Setting up shell environment..."
cat >> /home/pytracking/.bashrc << 'EOF'

# PyTracking aliases
alias pt-restart='sudo systemctl restart pytracking'
alias pt-status='sudo systemctl status pytracking'
alias pt-logs='sudo journalctl -u pytracking -f'
alias pt-nginx='sudo systemctl reload nginx'
alias pt-test='curl http://localhost:8000/health'

# Navigate to app directory quickly
alias pt-app='cd /home/pytracking/pytracking && source venv/bin/activate'

# Show tracking events
alias pt-events='sudo -u postgres psql pytracking -c "SELECT * FROM tracking_events ORDER BY created_at DESC LIMIT 10;"'

echo "PyTracking environment loaded. Use 'pt-app' to go to app directory."
EOF

chown pytracking:pytracking /home/pytracking/.bashrc

echo ""
echo "✅ Sudo permissions configured for pytracking user!"
echo ""
echo "🎯 The pytracking user can now:"
echo "   - Run service management commands without password"
echo "   - Use sudo for other commands (with password)"
echo "   - Access useful aliases (pt-restart, pt-status, etc.)"
echo ""
echo "🔄 To switch to pytracking user:"
echo "   su - pytracking"
echo ""
echo "📋 Available aliases for pytracking user:"
echo "   pt-restart  - Restart the PyTracking service"
echo "   pt-status   - Check service status"
echo "   pt-logs     - View live logs"
echo "   pt-nginx    - Reload nginx"
echo "   pt-test     - Test local connection"
echo "   pt-app      - Go to app directory and activate venv"
echo "   pt-events   - View recent tracking events"
