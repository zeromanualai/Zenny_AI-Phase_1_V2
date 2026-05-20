#!/bin/bash
# Test Shopify API connection
# Usage: ./test-shopify.sh <shop_domain> <access_token>

SHOP_DOMAIN=$1
ACCESS_TOKEN=$2

if [ -z "$SHOP_DOMAIN" ] || [ -z "$ACCESS_TOKEN" ]; then
  echo "Usage: ./test-shopify.sh <shop_domain> <access_token>"
  exit 1
fi

echo "Testing Shopify API for: $SHOP_DOMAIN"

curl -s -X GET \
  "https://${SHOP_DOMAIN}.myshopify.com/admin/api/2024-04/orders.json?limit=1" \
  -H "X-Shopify-Access-Token: ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" | jq '.orders[0] | {id, name, total_price}'

echo ""
echo "✅ If you see order data above, Shopify is connected."
