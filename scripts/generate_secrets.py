#!/usr/bin/env python3
"""
Generate secure secrets for production deployment
"""

import secrets
import string
import base64
from datetime import datetime

def generate_secret_key(length=64):
    """Generate a secure secret key"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_alphanumeric(length=32):
    """Generate alphanumeric string"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_encryption_key():
    """Generate a base64 encoded encryption key"""
    key = secrets.token_bytes(32)
    return base64.urlsafe_b64encode(key).decode()

def main():
    print("🔐 Generating Secure Secrets for Production")
    print("=" * 50)
    print(f"Generated at: {datetime.now().isoformat()}")
    print("=" * 50)
    print()
    
    # Database passwords
    postgres_password = generate_secret_key(32)
    redis_password = generate_secret_key(24)
    
    # Application secrets
    secret_key = generate_secret_key(64)
    jwt_secret = generate_secret_key(48)
    encryption_key = generate_encryption_key()
    
    # Webhook secrets
    shopify_webhook_secret = generate_alphanumeric(32)
    stripe_webhook_secret = generate_alphanumeric(32)
    
    # API keys (placeholders - get real ones from services)
    shopify_api_key = "GET_FROM_SHOPIFY_PARTNERS"
    shopify_api_secret = "GET_FROM_SHOPIFY_PARTNERS"
    
    print("# Database Credentials")
    print(f"POSTGRES_PASSWORD={postgres_password}")
    print(f"REDIS_PASSWORD={redis_password}")
    print()
    
    print("# Application Secrets")
    print(f"SECRET_KEY={secret_key}")
    print(f"JWT_SECRET_KEY={jwt_secret}")
    print(f"ENCRYPTION_KEY={encryption_key}")
    print()
    
    print("# Webhook Secrets")
    print(f"SHOPIFY_WEBHOOK_SECRET={shopify_webhook_secret}")
    print(f"STRIPE_WEBHOOK_SECRET={stripe_webhook_secret}")
    print()
    
    print("# API Keys (Replace with actual values)")
    print(f"SHOPIFY_API_KEY={shopify_api_key}")
    print(f"SHOPIFY_API_SECRET={shopify_api_secret}")
    print()
    
    print("⚠️  IMPORTANT:")
    print("1. Save these secrets in a secure password manager")
    print("2. Never commit these to version control")
    print("3. Use different secrets for each environment")
    print("4. Rotate secrets regularly")
    print("5. Get actual API keys from Shopify Partners Dashboard")
    
    # Save to .env.production if requested
    save = input("\nSave to .env.production? (y/N): ")
    if save.lower() == 'y':
        with open('.env.production', 'w') as f:
            f.write(f"# Generated at {datetime.now().isoformat()}\n")
            f.write(f"# WARNING: Keep this file secure and never commit to git!\n\n")
            f.write("# Database\n")
            f.write(f"POSTGRES_PASSWORD={postgres_password}\n")
            f.write(f"REDIS_PASSWORD={redis_password}\n\n")
            f.write("# Security\n")
            f.write(f"SECRET_KEY={secret_key}\n")
            f.write(f"JWT_SECRET_KEY={jwt_secret}\n")
            f.write(f"ENCRYPTION_KEY={encryption_key}\n\n")
            f.write("# Webhooks\n")
            f.write(f"SHOPIFY_WEBHOOK_SECRET={shopify_webhook_secret}\n")
            f.write(f"STRIPE_WEBHOOK_SECRET={stripe_webhook_secret}\n\n")
            f.write("# TODO: Add your actual API keys\n")
            f.write(f"SHOPIFY_API_KEY={shopify_api_key}\n")
            f.write(f"SHOPIFY_API_SECRET={shopify_api_secret}\n")
        print("✅ Saved to .env.production")
        print("📝 Remember to add .env.production to .gitignore!")

if __name__ == "__main__":
    main()
