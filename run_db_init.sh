#!/bin/bash

echo "Running database initialization on Railway..."

# Run the initialization script in the Railway environment
railway run --service Inventorysync python backend/init_database.py

echo "Database initialization complete!"
