#!/usr/bin/env python3
"""
Generate a secure webhook secret for Shopify webhooks
"""

import secrets
import string

def generate_webhook_secret(length=32):
    """Generate a secure random string for webhook verification"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

if __name__ == "__main__":
    secret = generate_webhook_secret()
    print(f"Generated webhook secret: {secret}")
    print(f"\nAdd this to your .env file:")
    print(f"SHOPIFY_WEBHOOK_SECRET={secret}")
    print(f"\nThis secret will be used to verify webhook authenticity from Shopify.")
