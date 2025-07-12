#!/bin/bash

# Initialize database tables
echo "Initializing database tables..."
python backend/init_database.py || echo "Database initialization completed or skipped"

# Start the application
echo "Starting InventorySync application..."
exec gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
