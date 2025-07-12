#!/bin/sh
set -e

echo "Starting InventorySync Backend (Production)..."

# Wait for PostgreSQL with timeout
echo "Waiting for PostgreSQL..."
timeout=60
counter=0
while ! pg_isready -h ${POSTGRES_HOST:-postgres} -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER:-inventorysync}
do
  counter=$((counter+1))
  if [ $counter -eq $timeout ]; then
    echo "ERROR: PostgreSQL connection timeout after ${timeout}s"
    exit 1
  fi
  echo "PostgreSQL is unavailable - sleeping (${counter}/${timeout})"
  sleep 1
done
echo "PostgreSQL is ready!"

# Wait for Redis with timeout
echo "Waiting for Redis..."
counter=0
while ! python -c "import redis; r = redis.Redis.from_url('${REDIS_URL}'); r.ping()"
do
  counter=$((counter+1))
  if [ $counter -eq $timeout ]; then
    echo "ERROR: Redis connection timeout after ${timeout}s"
    exit 1
  fi
  echo "Redis is unavailable - sleeping (${counter}/${timeout})"
  sleep 1
done
echo "Redis is ready!"

# Run database migrations
echo "Running database migrations..."
cd /app/backend
alembic upgrade head

# Collect static files if needed
if [ -d "/app/static" ]; then
    echo "Static files directory found"
fi

# Pre-compile Python files for faster startup
echo "Pre-compiling Python files..."
python -m compileall -q /app/backend

# Execute the main command
exec "$@"
