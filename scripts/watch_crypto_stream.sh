#!/bin/bash
# Watch live crypto trades streaming from Binance

echo "🚀 Live Crypto Trade Stream"
echo "═══════════════════════════════════════"
echo ""
echo "Streaming real trades from Binance..."
echo "Press Ctrl+C to stop"
echo ""

docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic streaming-events \
  --from-beginning \
  --max-messages 20 \
  2>/dev/null | python3 -c "
import sys
import json

for line in sys.stdin:
    try:
        trade = json.loads(line)
        symbol = trade['symbol']
        price = trade['price']
        qty = trade['quantity']
        
        # Add color based on symbol
        if 'BTC' in symbol:
            icon = '₿'
        elif 'ETH' in symbol:
            icon = 'Ξ'
        else:
            icon = '●'
        
        print(f'{icon} {symbol:10} | Price: \${price:>10,.2f} | Qty: {qty:.6f}')
    except:
        pass
"

echo ""
echo "═══════════════════════════════════════"
echo "This is real market data from Binance! 📈"

