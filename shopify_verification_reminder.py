#!/usr/bin/env python3
"""
Shopify Verification Status Reminder
This script provides periodic reminders to check your Shopify verification status
"""

import time
from datetime import datetime
import sys
import webbrowser

def main():
    print("Shopify Verification Status Reminder")
    print("=" * 50)
    print("\nThis will remind you to check your Shopify verification status periodically.")
    print("URL: https://admin.shopify.com/store/inventorysync-dev/settings/payments/setup")
    
    # Ask for check interval
    interval_minutes = input("\nHow often do you want to be reminded? (in minutes, default 5): ").strip()
    if not interval_minutes:
        interval_minutes = 5
    else:
        try:
            interval_minutes = int(interval_minutes)
        except ValueError:
            interval_minutes = 5
    
    check_interval = interval_minutes * 60  # Convert to seconds
    
    print(f"\nI'll remind you every {interval_minutes} minutes.")
    print("Press Ctrl+C to stop\n")
    
    # Option to open browser
    open_browser = input("Would you like me to open the URL in your browser each time? (y/n): ").lower().strip() == 'y'
    
    try:
        check_count = 1
        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n{'='*70}")
            print(f"[{timestamp}] Reminder #{check_count}")
            print(f"{'='*70}")
            print("🔔 Time to check your Shopify verification status!")
            print("\nGo to: https://admin.shopify.com/store/inventorysync-dev/settings/payments/setup")
            print("\nLook for:")
            print("  ✓ If you see 'Pending' - verification is still in progress")
            print("  ✓ If 'Pending' is gone and you can complete setup - verification is done!")
            
            if open_browser:
                try:
                    webbrowser.open("https://admin.shopify.com/store/inventorysync-dev/settings/payments/setup")
                    print("\n🌐 Opened in your browser!")
                except:
                    print("\n⚠️  Couldn't open browser automatically")
            
            print("\nCurrent status options:")
            print("  [p] Still Pending")
            print("  [c] Complete! Verification done")
            print("  [s] Skip this check")
            print("  [q] Quit")
            
            status = input("\nEnter status (p/c/s/q): ").lower().strip()
            
            if status == "c":
                print("\n🎉 Congratulations! Verification is complete!")
                print("✅ You can now start accepting payments with Shopify Payments.")
                print("\nNext steps:")
                print("1. Complete any remaining payment setup steps")
                print("2. Test a payment if in test mode")
                print("3. You're ready to go!")
                break
            elif status == "p":
                print(f"\n⏳ Still pending. I'll remind you again in {interval_minutes} minutes...")
            elif status == "q":
                print("\n👋 Stopping reminders. Good luck!")
                break
            elif status == "s":
                print("\n⏭️  Skipping this check...")
            else:
                print("\n❓ Invalid option, assuming still pending...")
            
            check_count += 1
            
            # Show countdown
            print(f"\n⏰ Next reminder in {interval_minutes} minutes...")
            print("   (Press Ctrl+C to stop)")
            
            # Sleep with a simple progress indicator
            for i in range(interval_minutes):
                remaining = interval_minutes - i
                print(f"\r   {remaining} minutes remaining...    ", end="", flush=True)
                time.sleep(60)
            
    except KeyboardInterrupt:
        print("\n\n👋 Stopped reminders. Check back later!")
        sys.exit(0)

if __name__ == "__main__":
    main()
