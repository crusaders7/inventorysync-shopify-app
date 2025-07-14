#!/usr/bin/env python3
"""
Generate secure keys for Railway environment variables
"""

import secrets
import string
import base64


def generate_secret_key(length=32):
    """Generate a secure secret key"""
    return secrets.token_urlsafe(length)


def generate_alphanumeric_key(length=32):
    """Generate an alphanumeric key"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_webhook_secret(length=24):
    """Generate a webhook secret"""
    return secrets.token_hex(length)


def main():
    print("=== Railway Environment Variable Key Generator ===\n")
    
    # Generate keys
    secret_key = generate_secret_key(32)
    jwt_secret = generate_secret_key(32)
    encryption_key = generate_secret_key(32)
    webhook_secret = generate_webhook_secret(24)
    
    # Database passwords
    postgres_password = generate_alphanumeric_key(24)
    redis_password = generate_alphanumeric_key(24)
    
    print("Copy these values to your Railway environment variables:\n")
    
    print("# Security Keys")
    print(f"SECRET_KEY={secret_key}")
    print(f"JWT_SECRET_KEY={jwt_secret}")
    print(f"ENCRYPTION_KEY={encryption_key}")
    print(f"SHOPIFY_WEBHOOK_SECRET={webhook_secret}")
    print()
    
    print("# Database Passwords (if not using Railway's auto-generated ones)")
    print(f"POSTGRES_PASSWORD={postgres_password}")
    print(f"REDIS_PASSWORD={redis_password}")
    print()
    
    print("# Complete Database URLs (replace with Railway's internal hostnames)")
    print(f"DATABASE_URL=postgresql://postgres:{postgres_password}@postgres.railway.internal:5432/railway")
    print(f"DATABASE_URL_ASYNC=postgresql+asyncpg://postgres:{postgres_password}@postgres.railway.internal:5432/railway")
    print(f"REDIS_URL=redis://default:{redis_password}@redis.railway.internal:6379")
    print()
    
    print("⚠️  IMPORTANT NOTES:")
    print("1. If Railway provides its own PostgreSQL/Redis instances, use their connection strings")
    print("2. Save these keys securely - they cannot be recovered once lost")
    print("3. Never commit these values to version control")
    print("4. Use Railway's environment variable management to store these securely")


if __name__ == "__main__":
    main()
