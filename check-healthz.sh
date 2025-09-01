#!/bin/bash

# Script to check when the healthz endpoint becomes available after deployment

API_URL="https://family-tree-api-klif7ymw3q-uc.a.run.app"
HEALTHZ_URL="$API_URL/healthz"

echo "Checking healthz endpoint availability..."
echo "URL: $HEALTHZ_URL"
echo "---"

MAX_ATTEMPTS=30
ATTEMPT=1

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    echo "Attempt $ATTEMPT/$MAX_ATTEMPTS..."

    # Check if endpoint returns 200
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTHZ_URL")

    if [ "$HTTP_STATUS" = "200" ]; then
        echo "✅ Success! healthz endpoint is now available"
        echo "Response:"
        curl -s "$HEALTHZ_URL" | jq '.' 2>/dev/null || curl -s "$HEALTHZ_URL"
        exit 0
    else
        echo "❌ Status: $HTTP_STATUS (not yet available)"
    fi

    # Wait before next attempt
    if [ $ATTEMPT -lt $MAX_ATTEMPTS ]; then
        echo "Waiting 30 seconds before next attempt..."
        sleep 30
    fi

    ATTEMPT=$((ATTEMPT + 1))
done

echo "❌ healthz endpoint still not available after $MAX_ATTEMPTS attempts"
echo "Check the CI/CD workflow status: gh run list --limit 5"
exit 1
