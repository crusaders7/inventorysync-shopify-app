#!/usr/bin/env python3
"""
Shopify Verification Status Checker
This script continuously checks the Shopify verification page status
"""

import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sys

def check_verification_status(url):
    """
    Check the verification status on the Shopify page
    Returns: 'pending', 'complete', or 'error'
    """
    try:
        # Make a request to the page
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for key phrases
        page_text = soup.get_text().lower()
        
        if "pending" in page_text and "submitted for verification" in page_text:
            return "pending"
        elif "complete account setup" in page_text and "pending" not in page_text:
            return "complete"
        else:
            # Try to extract any status message
            status_text = soup.get_text()[:200]  # First 200 chars for context
            return f"unknown: {status_text}"
            
    except requests.RequestException as e:
        return f"error: {str(e)}"

def main():
    # URL to check - you'll need to provide this
    print("Shopify Verification Status Checker")
    print("=" * 50)
    
    url = input("Enter the Shopify verification page URL: ").strip()
    
    if not url:
        print("Error: No URL provided")
        sys.exit(1)
    
    check_interval = 60  # Check every 60 seconds
    
    print(f"\nChecking verification status every {check_interval} seconds...")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status = check_verification_status(url)
            
            print(f"[{timestamp}] Status: {status}")
            
            if "complete" in status.lower():
                print("\n✅ Verification Complete! Account setup is done.")
                break
            elif "error" in status.lower():
                print(f"\n❌ Error checking status: {status}")
                retry = input("Retry? (y/n): ").lower()
                if retry != 'y':
                    break
            
            # Wait before next check
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        print("\n\nStopped checking.")
        sys.exit(0)

if __name__ == "__main__":
    main()
