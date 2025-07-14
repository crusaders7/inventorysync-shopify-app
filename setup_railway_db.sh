#!/bin/bash

echo "Setting up Railway database connections..."

# Get the project dashboard URL
PROJECT_URL=$(railway open --json | jq -r '.url' 2>/dev/null || echo "")

if [ -z "$PROJECT_URL" ]; then
    echo "Please visit your Railway dashboard to get the database connection strings:"
    echo "https://railway.com/project/de832abe-3d73-40ef-9fc5-c4054e8af06c"
    echo ""
    echo "Look for:"
    echo "1. PostgreSQL service - copy the DATABASE_URL"
    echo "2. Redis service - copy the REDIS_URL"
    echo ""
    echo "Then update your .env file with:"
    echo "DATABASE_URL=<your-postgresql-url>"
    echo "REDIS_URL=<your-redis-url>"
else
    echo "Opening Railway dashboard: $PROJECT_URL"
fi

echo ""
echo "After getting the URLs from Railway dashboard, you can test the connections with:"
echo "./test_db_connection.py"
