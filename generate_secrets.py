#!/usr/bin/env python3
"""Generate strong secrets for production environment"""

import secrets
import string
import base64

def generate_secret_key(length=64):
    """Generate a strong secret key"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_jwt_secret():
    """Generate a JWT secret"""
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8')

def generate_database_password(length=32):
    """Generate a strong database password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def main():
    print("=== Generated Production Secrets ===\n")
    
    print(f"SECRET_KEY={generate_secret_key()}")
    print(f"JWT_SECRET_KEY={generate_jwt_secret()}")
    print(f"DATABASE_PASSWORD={generate_database_password()}")
    print(f"SHOPIFY_API_SECRET={generate_secret_key(48)}")
    print(f"ENCRYPTION_KEY={base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8')}")
    print(f"REDIS_PASSWORD={generate_database_password(24)}")
    
    print("\n=== Instructions ===")
    print("1. Copy these values to your .env.production file")
    print("2. NEVER commit these secrets to version control")
    print("3. Use a secure secret management service in production")
    print("4. Rotate these secrets regularly")

if __name__ == "__main__":
    main()
