#!/bin/bash
# Zenny AI — Connection Test Script
# Run this after setup to verify all services are reachable

echo "🧪 Zenny Connection Test Suite"
echo "================================"

# Check Zenny Core health
echo ""
echo "1. Zenny Core Health Check..."
curl -s http://localhost:3000/health | jq . || echo "   ❌ Zenny Core not responding"

# Check Redis
echo ""
echo "2. Redis Connection..."
redis-cli -u redis://default:$REDIS_PASSWORD@$REDIS_HOST:$REDIS_PORT ping || echo "   ❌ Redis not responding"

# Check Supabase
echo ""
echo "3. Supabase Connection..."
curl -s "$SUPABASE_URL/rest/v1/" -H "apikey: $SUPABASE_ANON_KEY" | head -c 100 || echo "   ❌ Supabase not responding"

# Check n8n
echo ""
echo "4. n8n Health Check..."
curl -s http://$N8N_HOST:5678/healthz | head -c 100 || echo "   ❌ n8n not responding"

echo ""
echo "================================"
echo "Test complete."
