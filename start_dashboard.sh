#!/bin/bash
# Quinn Social Media Dashboard Startup Script

echo "🚀 Starting Quinn Social Media Dashboard..."
echo "📱 Dashboard will be available at: http://localhost:5001"
echo "🔄 Tweets will update every 5 minutes automatically"
echo ""

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not detected. Activating .venv..."
    source .venv/bin/activate
fi

# Check if dependencies are installed
if ! python -c "import flask, flask_socketio" 2>/dev/null; then
    echo "📦 Installing required dependencies..."
    pip install -r requirements.txt
fi

# Start the dashboard
echo "🎯 Starting Flask web app..."
python webapp.py
