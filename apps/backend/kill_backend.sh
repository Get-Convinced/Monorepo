#!/bin/bash
# Kill backend server forcefully

echo "🔍 Looking for backend processes..."

# Find processes on backend ports
PIDS_8082=$(lsof -ti :8082)
PIDS_8001=$(lsof -ti :8001)

# Find uvicorn processes
UVICORN_PIDS=$(pgrep -f "uvicorn.*src.main:app")

# Combine all PIDs
ALL_PIDS="$PIDS_8082 $PIDS_8001 $UVICORN_PIDS"

if [ -z "$ALL_PIDS" ]; then
    echo "✅ No backend processes found running"
    exit 0
fi

echo "🎯 Found processes: $ALL_PIDS"
echo "💀 Force killing..."

# Kill with SIGKILL (-9)
for PID in $ALL_PIDS; do
    if [ ! -z "$PID" ]; then
        kill -9 $PID 2>/dev/null && echo "   ✓ Killed PID $PID"
    fi
done

# Wait a moment
sleep 0.5

# Verify
if lsof -ti :8082 >/dev/null 2>&1 || lsof -ti :8001 >/dev/null 2>&1; then
    echo "⚠️  Some processes may still be running"
    echo "🔍 Check with: lsof -i :8082 or lsof -i :8001"
else
    echo "✅ All backend processes killed successfully"
fi
