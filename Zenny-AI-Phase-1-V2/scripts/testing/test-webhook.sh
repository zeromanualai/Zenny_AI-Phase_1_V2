#!/bin/bash
# Test Zenny Core webhook
# Usage: ./test-webhook.sh <client_slug> <message>

CLIENT_SLUG=$1
MESSAGE=${2:-"Where is my order?"}
ZENNY_API=${ZENNY_API_URL:-"http://localhost:3000"}

if [ -z "$CLIENT_SLUG" ]; then
  echo "Usage: ./test-webhook.sh <client_slug> [message]"
  exit 1
fi

echo "Testing webhook for client: $CLIENT_SLUG"
echo "Message: $MESSAGE"
echo ""

curl -s -X POST "${ZENNY_API}/v1/webhook?client_id=${CLIENT_SLUG}" \
  -H "Content-Type: application/json" \
  -d "{
    "client_id": "${CLIENT_SLUG}",
    "user_id": "test-user-123",
    "message": "${MESSAGE}",
    "intent": "order_status"
  }" | jq .

echo ""
