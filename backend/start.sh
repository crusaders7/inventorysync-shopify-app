#!/bin/bash

# Initialize database tables
echo "Initializing database tables..."
python -m backend.init_db || echo "Database initialization completed or skipped"

# Start the application
echo "Starting InventorySync application..."
exec gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
