#!/bin/bash

# Script to delete and re-sync all stocks with corrected UTC timestamps
# This fixes the timezone issue by removing old data and fetching fresh data

API_URL="http://localhost:8000"

echo "=========================================="
echo "Stock Re-sync Script"
echo "=========================================="
echo ""
echo "⚠️  WARNING: This will delete ALL candles and indicators for ALL stocks!"
echo "   (Trades and portfolio will NOT be affected)"
echo ""
read -p "Do you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Aborted by user"
    exit 0
fi

echo ""
echo "📊 Fetching list of all stocks..."
stocks=$(curl -s "$API_URL/stocks" | python3 -c "import sys, json; data = json.load(sys.stdin); print(' '.join([s['symbol'] for s in data]))")

if [ -z "$stocks" ]; then
    echo "❌ No stocks found or API is not responding"
    exit 1
fi

echo "Found stocks: $stocks"
echo ""

# Convert to array
stock_array=($stocks)
total=${#stock_array[@]}
current=0

echo "=========================================="
echo "Starting deletion and re-sync process..."
echo "=========================================="
echo ""

for symbol in $stocks; do
    current=$((current + 1))
    echo "[$current/$total] Processing $symbol..."
    echo "  ├─ Deleting old data..."
    
    delete_response=$(curl -s -X DELETE "$API_URL/stocks/$symbol")
    deleted_candles=$(echo "$delete_response" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('deleted', {}).get('candles', 0))" 2>/dev/null)
    
    if [ -z "$deleted_candles" ]; then
        echo "  ├─ ⚠️  Stock not found or already deleted"
    else
        echo "  ├─ ✅ Deleted $deleted_candles candles"
    fi
    
    echo "  ├─ Re-syncing with correct timestamps..."
    sync_response=$(curl -s -X POST "$API_URL/candles/$symbol/sync")
    
    # Extract summary
    new_candles=$(echo "$sync_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    results = data.get('results', [])
    total = sum(r.get('new_candles', 0) for r in results)
    print(total)
except:
    print('0')
" 2>/dev/null)
    
    if [ "$new_candles" -gt 0 ]; then
        echo "  └─ ✅ Synced $new_candles new candles"
    else
        echo "  └─ ⚠️  Sync completed but no candles added"
    fi
    
    echo ""
done

echo "=========================================="
echo "✅ Re-sync Complete!"
echo "=========================================="
echo ""
echo "Summary:"
echo "  • Total stocks processed: $total"
echo "  • All stocks now have UTC timestamps (OPEN time)"
echo "  • Frontend will display in IST automatically"
echo ""
echo "Next steps:"
echo "  1. Refresh your browser"
echo "  2. Check the charts - timestamps should match current IST time"
echo "  3. Verify latest candles are up-to-date"
echo ""

