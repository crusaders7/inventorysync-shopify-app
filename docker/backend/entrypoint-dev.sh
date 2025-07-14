#!/bin/sh
set -e

echo "Starting InventorySync Backend (Development)..."

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
while ! pg_isready -h ${POSTGRES_HOST:-postgres} -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER:-inventorysync}
do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done
echo "PostgreSQL is ready!"

# Wait for Redis
echo "Waiting for Redis..."
while ! nc -z ${REDIS_HOST:-redis} ${REDIS_PORT:-6379}
do
  echo "Redis is unavailable - sleeping"
  sleep 1
done
echo "Redis is ready!"

# Run database migrations
echo "Running database migrations..."
cd /app/backend
alembic upgrade head || echo "No migrations to run or alembic not configured"

# Create test data if requested
if [ "$CREATE_TEST_DATA" = "true" ]; then
    echo "Creating test data..."
    python -m backend.setup_test_data || echo "Test data creation skipped"
fi

# Execute the main command
exec "$@"
