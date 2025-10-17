#!/bin/bash

# Event Notification Cron Job Script for Family Tree
# This script calls the notification endpoint to send reminder emails
# Runs every 3 hours to catch users who enable notifications close to event dates
# Add this to your crontab to run automatically

# Configuration
API_BASE_URL="${API_BASE_URL:-http://localhost:8080}"
LOG_FILE="${LOG_FILE:-/var/log/family-tree-notifications.log}"
ADMIN_TOKEN="${ADMIN_TOKEN:-}"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to send notification
send_notifications() {
    log "Starting event notification run..."

    if [ -z "$ADMIN_TOKEN" ]; then
        log "ERROR: ADMIN_TOKEN environment variable not set"
        return 1
    fi

    # Call the notification endpoint
    response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        "$API_BASE_URL/events/notifications/send-reminders")

    # Parse response
    http_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | head -n -1)

    if [ "$http_code" = "200" ]; then
        # Parse JSON response to get sent count
        sent_count=$(echo "$response_body" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('sent', 0))" 2>/dev/null || echo "0")
        events_count=$(echo "$response_body" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('events_processed', 0))" 2>/dev/null || echo "0")

        log "SUCCESS: Sent $sent_count notifications for $events_count events"
        log "Response: $response_body"
    else
        log "ERROR: HTTP $http_code - $response_body"
        return 1
    fi
}

# Main execution
main() {
    log "=== Family Tree Event Notifications Cron Job ==="

    # Check if API is reachable
    if ! curl -s -f "$API_BASE_URL/health" >/dev/null 2>&1; then
        log "ERROR: API not reachable at $API_BASE_URL"
        exit 1
    fi

    # Send notifications
    if send_notifications; then
        log "Notification job completed successfully"
        exit 0
    else
        log "Notification job failed"
        exit 1
    fi
}

# Execute main function
main "$@"
