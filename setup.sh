#!/bin/bash

echo "========================================"
echo "  RoDork - Installation Script"
echo "========================================"
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
if [ -z "$python_version" ]; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi
echo "✅ Python $python_version detected"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate and install dependencies
echo ""
echo "📥 Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

# Check for .env file
echo ""
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit the .env file with your Shodan API key!"
    echo "   Get a free key at: https://account.shodan.io/register"
    echo ""
    echo "   nano .env"
else
    echo "✅ .env file already exists"
fi

# Check API key
echo ""
echo "🔑 Checking Shodan API key..."
python rodork.py --check-api 2>/dev/null || echo "   Run 'python rodork.py --check-api' after setting your key"

echo ""
echo "========================================"
echo "  Installation Complete!"
echo "========================================"
echo ""
echo "To activate the environment:"
echo "  source venv/bin/activate"
echo ""
echo "To run RoDork:"
echo "  python rodork.py"
echo ""
echo "To check your API connection:"
echo "  python rodork.py --check-api"
echo ""
