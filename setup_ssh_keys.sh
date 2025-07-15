#!/bin/bash
# SSH Key Management and Access Control
# Generate and deploy SSH keys for secure access

set -euo pipefail

echo "🔑 SSH Key Management for PyTracking Server"
echo "==========================================="

YOUR_IP="96.2.2.124"
SERVER_IP="143.110.214.80"
SSH_PORT="2222"
KEY_NAME="pytracking_server_key"

# Create SSH directory if it doesn't exist
mkdir -p ~/.ssh
chmod 700 ~/.ssh

echo "Generating SSH key pair for secure server access..."

# Generate SSH key pair
ssh-keygen -t ed25519 -f ~/.ssh/$KEY_NAME -C "pytracking-server-access-$(date +%Y%m%d)" -N ""

echo "✅ SSH key pair generated:"
echo "   Private key: ~/.ssh/$KEY_NAME"
echo "   Public key: ~/.ssh/$KEY_NAME.pub"

# Display public key
echo ""
echo "📋 Public Key (copy this to your server):"
echo "=========================================="
cat ~/.ssh/$KEY_NAME.pub
echo ""

# Create SSH config entry
echo "📝 Adding SSH config entry..."
cat >> ~/.ssh/config << EOF

# PyTracking Server Access
Host pytracking-server
    HostName $SERVER_IP
    Port $SSH_PORT
    User root
    IdentityFile ~/.ssh/$KEY_NAME
    IdentitiesOnly yes
    ServerAliveInterval 60
    ServerAliveCountMax 3
    StrictHostKeyChecking ask
    UserKnownHostsFile ~/.ssh/known_hosts_pytracking

Host realproductpat.com
    HostName $SERVER_IP
    Port $SSH_PORT
    User root
    IdentityFile ~/.ssh/$KEY_NAME
    IdentitiesOnly yes
    ServerAliveInterval 60
    ServerAliveCountMax 3
EOF

echo "✅ SSH config updated"

# Set proper permissions
chmod 600 ~/.ssh/$KEY_NAME
chmod 644 ~/.ssh/$KEY_NAME.pub
chmod 600 ~/.ssh/config

echo ""
echo "🚀 Next Steps:"
echo "=============="
echo "1. Copy the public key above"
echo "2. Run this on your server:"
echo ""
echo "   mkdir -p ~/.ssh"
echo "   echo 'PASTE_PUBLIC_KEY_HERE' >> ~/.ssh/authorized_keys"
echo "   chmod 700 ~/.ssh"
echo "   chmod 600 ~/.ssh/authorized_keys"
echo ""
echo "3. Test connection:"
echo "   ssh pytracking-server"
echo ""
echo "4. Deploy hardening script:"
echo "   scp enterprise_hardening.sh pytracking-server:/root/"
echo "   ssh pytracking-server 'chmod +x /root/enterprise_hardening.sh && /root/enterprise_hardening.sh'"

# Create deployment script
cat > deploy_hardening.sh << 'EOF'
#!/bin/bash
# Deploy hardening to PyTracking server

echo "🚀 Deploying enterprise hardening to PyTracking server..."

# Upload all security files
scp enterprise_hardening.sh pytracking-server:/root/
scp security_dashboard.sh pytracking-server:/root/
scp advanced_honeypot.py pytracking-server:/root/

# Make scripts executable
ssh pytracking-server 'chmod +x /root/*.sh /root/*.py'

echo "✅ Files uploaded. To run hardening:"
echo "ssh pytracking-server '/root/enterprise_hardening.sh'"
EOF

chmod +x deploy_hardening.sh

echo ""
echo "🔧 Quick Deploy Command Created:"
echo "   ./deploy_hardening.sh"
echo ""
echo "🔒 Security Note: Keep your private key secure!"
echo "   Private key location: ~/.ssh/$KEY_NAME"
