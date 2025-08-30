#!/bin/bash
cd "$(dirname "$0")"
echo "🧪 Testing automation setup..."
echo "Current directory: $(pwd)"
echo "Python version: $(python --version)"
echo "Virtual environment: $VIRTUAL_ENV"
echo "Testing main.py..."
python main.py
echo "✅ Test completed"
