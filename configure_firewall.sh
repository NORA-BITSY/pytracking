#!/bin/bash
# Configure firewall for PyTracking server
# Run as root on your server

echo "🔥 Configuring Firewall for PyTracking"
echo "======================================"

# Check if ufw is installed and active
if command -v ufw >/dev/null 2>&1; then
    echo "1. Configuring UFW firewall..."
    
    # Reset to defaults
    ufw --force reset
    
    # Set default policies
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow SSH (port 22) - CRITICAL: Don't lock yourself out!
    ufw allow 22/tcp
    
    # Allow HTTP (port 80)
    ufw allow 80/tcp
    
    # Allow HTTPS (port 443)
    ufw allow 443/tcp
    
    # Allow PostgreSQL for local connections only
    ufw allow from 127.0.0.1 to any port 5432
    
    # Enable the firewall
    ufw --force enable
    
    # Show status
    ufw status verbose
    
elif command -v iptables >/dev/null 2>&1; then
    echo "1. Configuring iptables firewall..."
    
    # Flush existing rules
    iptables -F
    iptables -X
    iptables -t nat -F
    iptables -t nat -X
    iptables -t mangle -F
    iptables -t mangle -X
    
    # Set default policies
    iptables -P INPUT DROP
    iptables -P FORWARD DROP
    iptables -P OUTPUT ACCEPT
    
    # Allow loopback
    iptables -A INPUT -i lo -j ACCEPT
    iptables -A OUTPUT -o lo -j ACCEPT
    
    # Allow established connections
    iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
    
    # Allow SSH (port 22)
    iptables -A INPUT -p tcp --dport 22 -j ACCEPT
    
    # Allow HTTP (port 80)
    iptables -A INPUT -p tcp --dport 80 -j ACCEPT
    
    # Allow HTTPS (port 443)
    iptables -A INPUT -p tcp --dport 443 -j ACCEPT
    
    # Save rules (Ubuntu/Debian)
    if command -v iptables-save >/dev/null 2>&1; then
        iptables-save > /etc/iptables/rules.v4
    fi
    
    echo "iptables rules configured"
    
else
    echo "No firewall detected (ufw or iptables)"
fi

echo ""
echo "2. Checking if ports are now accessible..."

# Test if nginx is running and accessible
if systemctl is-active nginx >/dev/null 2>&1; then
    echo "✅ Nginx is running"
else
    echo "❌ Nginx is not running - starting it..."
    systemctl start nginx
fi

# Test if our pytracking service is running
if systemctl is-active pytracking >/dev/null 2>&1; then
    echo "✅ PyTracking service is running"
else
    echo "❌ PyTracking service is not running - starting it..."
    systemctl start pytracking
fi

echo ""
echo "3. Testing local connections..."
sleep 2

# Test Flask app directly
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ Flask app responding on port 8000"
else
    echo "❌ Flask app not responding on port 8000"
fi

# Test nginx proxy
if curl -s http://localhost/health >/dev/null 2>&1; then
    echo "✅ Nginx proxy working on port 80"
else
    echo "❌ Nginx proxy not working on port 80"
fi

echo ""
echo "4. Current firewall status:"
if command -v ufw >/dev/null 2>&1; then
    ufw status
elif command -v iptables >/dev/null 2>&1; then
    iptables -L INPUT -n
fi

echo ""
echo "5. Services status:"
systemctl status nginx --no-pager -l
systemctl status pytracking --no-pager -l

echo ""
echo "🎯 Firewall configured! Now test from external:"
echo "From your local machine, try:"
echo "  curl http://143.110.214.80/health"
echo ""
echo "If that works, then configure DNS for realproductpat.com"
