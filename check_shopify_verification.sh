#!/bin/bash

# Shopify Verification Status Checker

echo "Shopify Verification Status Checker"
echo "===================================="
echo

# Get the URL from user
read -p "Enter the Shopify verification page URL: " URL

if [ -z "$URL" ]; then
    echo "Error: No URL provided"
    exit 1
fi

CHECK_INTERVAL=60  # Check every 60 seconds

echo
echo "Checking verification status every $CHECK_INTERVAL seconds..."
echo "Press Ctrl+C to stop"
echo

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Fetch the page content
    CONTENT=$(curl -s "$URL" 2>/dev/null)
    
    if [ $? -ne 0 ]; then
        echo "[$TIMESTAMP] Status: Error connecting to the URL"
    else
        # Check for specific text patterns
        if echo "$CONTENT" | grep -qi "pending" && echo "$CONTENT" | grep -qi "submitted for verification"; then
            echo "[$TIMESTAMP] Status: Pending - Your information has been submitted for verification"
        elif echo "$CONTENT" | grep -qi "complete account setup" && ! echo "$CONTENT" | grep -qi "pending"; then
            echo "[$TIMESTAMP] Status: ✅ Verification Complete! Account setup is done."
            echo
            echo "Verification process is complete. You can now start accepting payments!"
            break
        else
            # Extract a snippet of the page for context
            SNIPPET=$(echo "$CONTENT" | grep -i -E "(verification|account|setup|pending|complete)" | head -1)
            echo "[$TIMESTAMP] Status: Unknown - $SNIPPET"
        fi
    fi
    
    # Wait before next check
    sleep $CHECK_INTERVAL
done
