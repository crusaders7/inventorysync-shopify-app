-- InventorySync Database Initialization Script
-- This script sets up the initial database configuration

-- Create database user (if not exists)
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'inventorysync_user') THEN

      CREATE ROLE inventorysync_user LOGIN PASSWORD 'secure_password_change_me';
   END IF;
END
$do$;

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE inventorysync TO inventorysync_user;

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search optimization

-- Set timezone
SET timezone = 'UTC';