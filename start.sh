#!/bin/bash
# Ophelia AI 2.0 - Railway Deployment Script
set -e

echo "🚀 Starting Ophelia AI 2.0..."

# Navigate to bot directory
cd discord-ai-bot

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found, using environment variables..."
    
    # Create .env from environment variables (Railway sets these)
    cat > .env << EOF
DISCORD_TOKEN=${DISCORD_TOKEN:-}
GROQ_API_KEYS=${GROQ_API_KEYS:-}
SUPABASE_URL=${SUPABASE_URL:-}
SUPABASE_KEY=${SUPABASE_KEY:-}
OWNER_IDS=${OWNER_IDS:-1169492860278669312,1463113729959919801,1443836576802013316}
DEFAULT_MODEL=${DEFAULT_MODEL:-llama-3.3-70b-versatile}
MAX_CONVERSATION_HISTORY=${MAX_CONVERSATION_HISTORY:-50}
CACHE_TTL=${CACHE_TTL:-3600}
LOG_LEVEL=${LOG_LEVEL:-INFO}
EOF
    
    echo "✅ Created .env from environment variables"
fi

# Run the bot
echo "🤖 Launching Ophelia AI 2.0..."
exec python bot.py
