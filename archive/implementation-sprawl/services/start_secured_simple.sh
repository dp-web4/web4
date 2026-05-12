#!/bin/bash
#
# Start all secured Web4 services for Phase 1 testing (Simple version)
# Uses direct Python execution instead of uvicorn module loading to avoid Prometheus registry issues
#

set -e

echo "Starting Web4 Secured Services (Phase 1 - Simple Mode)"
echo "========================================================="
echo ""

# Kill any existing service processes
echo "Cleaning up any existing service processes..."
pkill -f '_service_secured.py' 2>/dev/null || true
sleep 1

# Service ports (secured versions on 810x)
export WEB4_IDENTITY_PORT=8101
export WEB4_REPUTATION_PORT=8104
export WEB4_RESOURCES_PORT=8105
export WEB4_KNOWLEDGE_PORT=8106
export WEB4_IDENTITY_WORKERS=1
export WEB4_REPUTATION_WORKERS=1
export WEB4_RESOURCES_WORKERS=1
export WEB4_KNOWLEDGE_WORKERS=1

# TEST_MODE support (inherit from environment if set)
if [ -n "$WEB4_TEST_MODE" ]; then
    export WEB4_TEST_MODE
    echo "🧪 TEST_MODE enabled: $WEB4_TEST_MODE"
    echo "   Genesis witnesses will be accepted for testing"
fi

# Check if ports are available
for port in 8101 8104 8105 8106; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  Port $port is already in use"
        lsof -Pi :$port -sTCP:LISTEN
        exit 1
    fi
done

cd /home/dp/ai-workspace/web4/web4-standard/implementation/services

# Start services in background with output to log files
echo "Starting Identity Service (Secured) on port $WEB4_IDENTITY_PORT..."
nohup python3 -u identity_service_secured.py > identity_secured.log 2>&1 &
IDENTITY_PID=$!
echo "  PID: $IDENTITY_PID"

sleep 3

echo "Starting Reputation Service (Secured) on port $WEB4_REPUTATION_PORT..."
nohup python3 -u reputation_service_secured.py > reputation_secured.log 2>&1 &
REPUTATION_PID=$!
echo "  PID: $REPUTATION_PID"

sleep 3

echo "Starting Resources Service (Secured) on port $WEB4_RESOURCES_PORT..."
nohup python3 -u resources_service_secured.py > resources_secured.log 2>&1 &
RESOURCES_PID=$!
echo "  PID: $RESOURCES_PID"

sleep 3

echo "Starting Knowledge Service (Secured) on port $WEB4_KNOWLEDGE_PORT..."
nohup python3 -u knowledge_service_secured.py > knowledge_secured.log 2>&1 &
KNOWLEDGE_PID=$!
echo "  PID: $KNOWLEDGE_PID"

sleep 5

# Check if services are actually running
echo ""
echo "Checking service health..."
for pid in $IDENTITY_PID $REPUTATION_PID $RESOURCES_PID $KNOWLEDGE_PID; do
    if ! ps -p $pid > /dev/null 2>&1; then
        echo "❌ Process $pid died. Check logs for errors."
        exit 1
    fi
done

echo ""
echo "========================================================="
echo "✅ All secured services started!"
echo ""
echo "Service URLs:"
echo "  Identity:   http://localhost:8101/docs"
echo "  Reputation: http://localhost:8104/docs"
echo "  Resources:  http://localhost:8105/docs"
echo "  Knowledge:  http://localhost:8106/docs"
echo ""
echo "PIDs:"
echo "  Identity:   $IDENTITY_PID"
echo "  Reputation: $REPUTATION_PID"
echo "  Resources:  $RESOURCES_PID"
echo "  Knowledge:  $KNOWLEDGE_PID"
echo ""
echo "Log files:"
echo "  identity_secured.log"
echo "  reputation_secured.log"
echo "  resources_secured.log"
echo "  knowledge_secured.log"
echo ""
echo "To stop all services:"
echo "  kill $IDENTITY_PID $REPUTATION_PID $RESOURCES_PID $KNOWLEDGE_PID"
echo ""
echo "Or use: pkill -f '_service_secured.py'"
echo ""
echo "To view logs in real-time:"
echo "  tail -f identity_secured.log"
echo ""
