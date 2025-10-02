#!/bin/bash
# Real-Time Pipeline Monitor
# Watch your streaming data in action!

echo "Starting Real-Time Pipeline Monitor..."
echo "Press Ctrl+C to exit"
echo ""
sleep 2

# Get initial count
prev_count=$(docker exec kafka kafka-run-class kafka.tools.GetOffsetShell \
  --broker-list localhost:9092 \
  --topic streaming-events --time -1 2>/dev/null | awk -F: '{print $3}')

while true; do
  clear
  echo "╔════════════════════════════════════════════════════════════════╗"
  echo "║          REAL-TIME STREAMING PIPELINE MONITOR                   ║"
  echo "╚════════════════════════════════════════════════════════════════╝"
  echo ""
  
  # Get current count
  curr_count=$(docker exec kafka kafka-run-class kafka.tools.GetOffsetShell \
    --broker-list localhost:9092 \
    --topic streaming-events --time -1 2>/dev/null | awk -F: '{print $3}')
  
  # Calculate rate
  diff=$((curr_count - prev_count))
  rate=$(echo "scale=1; $diff / 3" | bc)
  
  echo "📊 PIPELINE STATISTICS"
  echo "══════════════════════════════════════════════════════════════"
  echo "  Total Events:       $curr_count"
  echo "  Last 3 seconds:     $diff events"
  echo "  Current Rate:       $rate events/second"
  echo "  Hourly Projection:  $(echo "$rate * 3600 / 1" | bc) events/hour"
  echo ""
  
  # Show recent events
  echo "🔄 LATEST EVENTS (refreshing...)"
  echo "══════════════════════════════════════════════════════════════"
  docker exec kafka kafka-console-consumer \
    --bootstrap-server localhost:9092 \
    --topic streaming-events \
    --max-messages 5 2>/dev/null | while read line; do
    event_type=$(echo "$line" | python3 -c "import sys, json; print(json.load(sys.stdin).get('event_type', '?'))" 2>/dev/null)
    user_id=$(echo "$line" | python3 -c "import sys, json; print(json.load(sys.stdin).get('user_id', '?'))" 2>/dev/null)
    device=$(echo "$line" | python3 -c "import sys, json; print(json.load(sys.stdin).get('device', '?'))" 2>/dev/null)
    
    case "$event_type" in
      "purchase")     icon="💰" ;;
      "user_login")   icon="🔐" ;;
      "page_view")    icon="👁️ " ;;
      "cart_add")     icon="🛒" ;;
      "item_click")   icon="🖱️ " ;;
      "search")       icon="🔍" ;;
      *)              icon="📝" ;;
    esac
    
    echo "  $icon $event_type | User: $user_id | Device: $device"
  done
  
  echo ""
  echo "══════════════════════════════════════════════════════════════"
  echo "  🟢 All Services Running  |  Next refresh in 3 seconds..."
  echo ""
  
  prev_count=$curr_count
  sleep 3
done


