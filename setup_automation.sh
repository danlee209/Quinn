#!/bin/bash

# Setup script for automating social media posting
echo "🚀 Setting up local automation for Quinn Social Media Bot"

# Create logs directory
mkdir -p logs
echo "📁 Created logs directory"

# Create a simple log rotation script
cat > rotate_logs.sh << 'EOF'
#!/bin/bash
# Rotate logs to prevent them from getting too large
cd "$(dirname "$0")"
if [ -f "logs/cron.log" ] && [ $(stat -f%z "logs/cron.log") -gt 10485760 ]; then
    mv logs/cron.log "logs/cron.log.$(date +%Y%m%d_%H%M%S)"
    echo "Log rotated at $(date)" > logs/cron.log
fi
EOF

chmod +x rotate_logs.sh
echo "📝 Created log rotation script"

# Create a test script to verify everything works
cat > test_automation.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
echo "🧪 Testing automation setup..."
echo "Current directory: $(pwd)"
echo "Python version: $(python --version)"
echo "Virtual environment: $VIRTUAL_ENV"
echo "Testing main.py..."
python main.py
echo "✅ Test completed"
EOF

chmod +x test_automation.sh
echo "🧪 Created test script"

# Instructions for cron setup
echo ""
echo "📋 Next Steps:"
echo "1. Test the setup: ./test_automation.sh"
echo "2. Set up cron job: crontab -e"
echo "3. Add this line to run at 9am daily:"
echo "   0 9 * * * cd $(pwd) && $(pwd)/.venv/bin/python main.py >> $(pwd)/logs/cron.log 2>&1"
echo ""
echo "4. Optional: Add log rotation to run weekly:"
echo "   0 0 * * 0 $(pwd)/rotate_logs.sh"
echo ""
echo "🔍 To monitor: tail -f logs/cron.log"
echo "📅 To test cron: date && crontab -l"
echo ""
echo "✅ Local automation setup complete!"
