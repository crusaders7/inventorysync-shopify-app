#!/bin/bash

echo "Starting Backend Server..."
echo "========================"

# Navigate to backend directory
cd /home/brend/inventorysync-shopify-app/backend

# Check if .env file exists and has DATABASE_URL
if [ -f .env ] && grep -q "^DATABASE_URL=" .env; then
    echo "Using DATABASE_URL from .env file"
    echo "(Config shows user: inventorysync, password: devpassword123)"
    source venv/bin/activate
    python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
else
    # Prompt for database password
    echo "No DATABASE_URL found in .env, prompting for password..."
    echo -n "Enter database password (try 'dbpassword-dev' or 'devpassword123'): "
    read -s DB_PASSWORD
    echo ""
    
    # Export the database URL with the password
    export DATABASE_URL="postgresql://postgres:${DB_PASSWORD}@localhost/inventorysync"
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Run the server
    echo "Starting server on http://localhost:8000"
    python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
fi
