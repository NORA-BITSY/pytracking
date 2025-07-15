#!/bin/bash
# Security Status Dashboard and Quick Commands
# Run this script to check security status

echo "🔒 PyTracking Server Security Dashboard"
echo "======================================="
echo "Server: 143.110.214.80 (realproductpat.com)"
echo "Date: $(date)"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

check_service() {
    if systemctl is-active --quiet $1; then
        echo -e "✅ $1: ${GREEN}ACTIVE${NC}"
    else
        echo -e "❌ $1: ${RED}INACTIVE${NC}"
    fi
}

echo "🛡️  SECURITY SERVICES STATUS:"
echo "----------------------------"
check_service "fail2ban"
check_service "ufw"
check_service "auditd"
check_service "pytracking-security-monitor"
check_service "endlessh"
check_service "sshd"
check_service "nginx"
check_service "pytracking"

echo ""
echo "🔥 FIREWALL STATUS:"
echo "-------------------"
ufw status

echo ""
echo "🕷️  ACTIVE HONEYPOTS:"
echo "--------------------"
netstat -tulpn | grep ":22 " | head -5
netstat -tulpn | grep ":2223 " | head -5

echo ""
echo "🚫 BLOCKED IPS (Last 20):"
echo "-------------------------"
iptables -L INPUT -n | grep DROP | tail -20

echo ""
echo "⚠️  RECENT THREATS (Last 10):"
echo "-----------------------------"
if [ -f /var/log/security/security_monitor.log ]; then
    grep "SECURITY ALERT" /var/log/security/security_monitor.log | tail -10
else
    echo "No threats detected"
fi

echo ""
echo "🔍 SYSTEM INTEGRITY:"
echo "-------------------"
echo "Last AIDE check: $(stat -c %y /var/lib/aide/aide.db 2>/dev/null || echo 'Not run')"
echo "Audit log size: $(du -h /var/log/audit/audit.log 2>/dev/null | cut -f1 || echo 'N/A')"

echo ""
echo "📊 SECURITY METRICS:"
echo "-------------------"
echo "SSH attempts today: $(grep "$(date '+%b %d')" /var/log/auth.log | grep -c "Failed password" || echo 0)"
echo "Web requests today: $(grep "$(date '+%d/%b/%Y')" /var/log/nginx/access.log | wc -l || echo 0)"
echo "Security alerts today: $(grep "$(date '+%Y-%m-%d')" /var/log/security/security_monitor.log | grep -c "ALERT" || echo 0)"

echo ""
echo "🔧 QUICK COMMANDS:"
echo "-----------------"
echo "View live security log: tail -f /var/log/security/security_monitor.log"
echo "Check blocked IPs: iptables -L INPUT -n | grep DROP"
echo "Unblock IP: iptables -D INPUT -s [IP] -j DROP"
echo "View honeypot activity: tail -f /var/log/security/honeypot.log"
echo "Security report: cat /var/log/security/hardening-report.txt"
echo "SSH connection: ssh -p 2222 root@143.110.214.80"

echo ""
echo "📧 Emergency Contact: admin@realproductpat.com"
echo "🆘 Support: Review /var/log/security/ for detailed logs"
