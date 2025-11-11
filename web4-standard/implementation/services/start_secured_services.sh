#!/bin/bash
#
# Start all secured Web4 services for Phase 1 testing
#
# Usage: ./start_secured_services.sh
#

set -e

echo "Starting Web4 Secured Services (Phase 1)"
echo "========================================"
echo ""

# Service ports (secured versions on 810x)
IDENTITY_PORT=8101
REPUTATION_PORT=8104
RESOURCES_PORT=8105
KNOWLEDGE_PORT=8106

# Check if ports are available
for port in $IDENTITY_PORT $REPUTATION_PORT $RESOURCES_PORT $KNOWLEDGE_PORT; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  Port $port is already in use"
        echo "   Kill existing process or choose different port"
        exit 1
    fi
done

# Start services in background
echo "Starting Identity Service (Secured) on port $IDENTITY_PORT..."
WEB4_IDENTITY_PORT=$IDENTITY_PORT python3 identity_service_secured.py &
IDENTITY_PID=$!
echo "  PID: $IDENTITY_PID"

sleep 2

echo "Starting Reputation Service (Secured) on port $REPUTATION_PORT..."
WEB4_REPUTATION_PORT=$REPUTATION_PORT python3 reputation_service_secured.py &
REPUTATION_PID=$!
echo "  PID: $REPUTATION_PID"

sleep 2

echo "Starting Resources Service (Secured) on port $RESOURCES_PORT..."
WEB4_RESOURCES_PORT=$RESOURCES_PORT python3 resources_service_secured.py &
RESOURCES_PID=$!
echo "  PID: $RESOURCES_PID"

sleep 2

echo "Starting Knowledge Service (Secured) on port $KNOWLEDGE_PORT..."
WEB4_KNOWLEDGE_PORT=$KNOWLEDGE_PORT python3 knowledge_service_secured.py &
KNOWLEDGE_PID=$!
echo "  PID: $KNOWLEDGE_PID"

sleep 3

echo ""
echo "========================================"
echo "✅ All secured services started!"
echo ""
echo "Service URLs:"
echo "  Identity:   http://localhost:$IDENTITY_PORT/docs"
echo "  Reputation: http://localhost:$REPUTATION_PORT/docs"
echo "  Resources:  http://localhost:$RESOURCES_PORT/docs"
echo "  Knowledge:  http://localhost:$KNOWLEDGE_PORT/docs"
echo ""
echo "PIDs:"
echo "  Identity:   $IDENTITY_PID"
echo "  Reputation: $REPUTATION_PID"
echo "  Resources:  $RESOURCES_PID"
echo "  Knowledge:  $KNOWLEDGE_PID"
echo ""
echo "To stop all services:"
echo "  kill $IDENTITY_PID $REPUTATION_PID $RESOURCES_PID $KNOWLEDGE_PID"
echo ""
echo "Or use: pkill -f 'python3.*_service_secured.py'"
echo ""
