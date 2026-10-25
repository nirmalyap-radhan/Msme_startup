#!/usr/bin/env bash
# ==============================================================================
# UDYOG SATHI — UNIFIED BUILD & RUN SCRIPT
# ==============================================================================
# Instantly prepares the environment, verifies dependencies, checks the database,
# and starts the production-ready Udyog Sathi server at http://localhost:8000.
#
# Usage:
#   ./build.sh          -> Builds environment, verifies database, runs server
#   ./build.sh --daemon -> Runs server in background (daemon mode)
#   ./build.sh --stop   -> Stops any running Udyog Sathi server instance
#   ./build.sh --status -> Checks health and running state
#   ./build.sh --test   -> Runs full pytest test suite
# ==============================================================================

set -e

# Change to script directory (project root)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Text Styling
BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

PORT=8000
HOST="0.0.0.0"
PID_FILE="$PROJECT_ROOT/data/server.pid"
DB_FILE="$PROJECT_ROOT/data/udyog_sathi.db"

# ------------------------------------------------------------------------------
# 1. Helper Functions
# ------------------------------------------------------------------------------
find_python() {
    if [ -n "$VIRTUAL_ENV" ] && [ -x "$VIRTUAL_ENV/bin/python" ]; then
        echo "$VIRTUAL_ENV/bin/python"
    elif [ -x "$PROJECT_ROOT/.venv/bin/python" ]; then
        echo "$PROJECT_ROOT/.venv/bin/python"
    elif [ -x "$PROJECT_ROOT/venv/bin/python" ]; then
        echo "$PROJECT_ROOT/venv/bin/python"
    elif [ -x "/opt/homebrew/bin/python3.11" ]; then
        echo "/opt/homebrew/bin/python3.11"
    elif [ -x "/usr/local/bin/python3.11" ]; then
        echo "/usr/local/bin/python3.11"
    elif command -v python3 >/dev/null 2>&1; then
        echo "$(command -v python3)"
    else
        echo ""
    fi
}

PYTHON_BIN=$(find_python)

if [ -z "$PYTHON_BIN" ]; then
    echo -e "${RED}[ERROR] Python 3.10+ was not found on your system.${NC}"
    exit 1
fi

stop_server() {
    echo -e "${YELLOW}[Udyog Sathi] Stopping running instances on port $PORT...${NC}"
    # Check pid file
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID" 2>/dev/null || true
            sleep 1
        fi
        rm -f "$PID_FILE"
    fi

    # Kill anything still holding port 8000
    PIDS_ON_PORT=$(lsof -ti :$PORT 2>/dev/null || true)
    if [ -n "$PIDS_ON_PORT" ]; then
        echo -e "${YELLOW}[Udyog Sathi] Freeing port $PORT (PIDs: $PIDS_ON_PORT)...${NC}"
        kill -9 $PIDS_ON_PORT 2>/dev/null || true
        sleep 1
    fi
    echo -e "${GREEN}[Udyog Sathi] Port $PORT is clean.${NC}"
}

check_status() {
    echo -e "${BLUE}=== Udyog Sathi System Status ===${NC}"
    if curl -s -f "http://127.0.0.1:$PORT/health/ready" >/dev/null 2>&1; then
        HEALTH_JSON=$(curl -s "http://127.0.0.1:$PORT/health/ready")
        echo -e "${GREEN}✓ Server is ACTIVE and healthy on http://127.0.0.1:$PORT${NC}"
        echo -e "Health Details: $HEALTH_JSON"
    else
        echo -e "${YELLOW}Server is not currently responding on http://127.0.0.1:$PORT${NC}"
    fi
}

# ------------------------------------------------------------------------------
# 2. Command Line Arguments Dispatch
# ------------------------------------------------------------------------------
case "$1" in
    --stop|stop)
        stop_server
        exit 0
        ;;
    --status|status)
        check_status
        exit 0
        ;;
    --test|test)
        echo -e "${BLUE}[Udyog Sathi] Executing Test Suite...${NC}"
        PYTHONPATH=. "$PYTHON_BIN" -m pytest tests/unit/ -v
        exit 0
        ;;
    --clean|clean)
        stop_server
        echo -e "${YELLOW}[Udyog Sathi] Cleaning cache and locks...${NC}"
        rm -f "$PROJECT_ROOT/data/scheduler.lock"
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
        echo -e "${GREEN}[Udyog Sathi] Clean completed.${NC}"
        exit 0
        ;;
esac

# ------------------------------------------------------------------------------
# 3. Environment Preparation
# ------------------------------------------------------------------------------
echo -e "${BLUE}================================================================${NC}"
echo -e "${BOLD}${GREEN}  UDYOG SATHI | ଉଦ୍ୟୋଗ ସାଥୀ — Production Engine Starter${NC}"
echo -e "${BLUE}================================================================${NC}"
echo -e "Using Python: ${BOLD}$PYTHON_BIN${NC}"

# Check .env
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${YELLOW}[Udyog Sathi] .env not found. Initializing from .env.example...${NC}"
    cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
fi

# Ensure data directories exist
mkdir -p "$PROJECT_ROOT/data/raw"
mkdir -p "$PROJECT_ROOT/data/backups"

# Check required core dependencies
if ! "$PYTHON_BIN" -c "import fastapi, uvicorn, sqlalchemy, pydantic" 2>/dev/null; then
    echo -e "${YELLOW}[Udyog Sathi] Installing missing dependencies from requirements.txt...${NC}"
    "$PYTHON_BIN" -m pip install -q -r "$PROJECT_ROOT/requirements.txt"
fi

# Check database tables
if [ ! -f "$DB_FILE" ]; then
    echo -e "${YELLOW}[Udyog Sathi] Initializing database tables...${NC}"
    PYTHONPATH=. "$PYTHON_BIN" -c "from services.scheme_ingestion.storage import SchemeStorageRepository; SchemeStorageRepository().create_tables()"
fi

# Free port 8000 if occupied by a stale server
PIDS_ON_PORT=$(lsof -ti :$PORT 2>/dev/null || true)
if [ -n "$PIDS_ON_PORT" ]; then
    echo -e "${YELLOW}[Udyog Sathi] Port $PORT in use by PID(s): $PIDS_ON_PORT. Recycling...${NC}"
    kill -9 $PIDS_ON_PORT 2>/dev/null || true
    sleep 1
fi

# Remove stale scheduler lock
rm -f "$PROJECT_ROOT/data/scheduler.lock"

# ------------------------------------------------------------------------------
# 4. Launch Application
# ------------------------------------------------------------------------------
echo -e "\n${GREEN}[Udyog Sathi] Launching FastAPI Web Application...${NC}"
echo -e "  🌐 Local Web Portal:      ${BOLD}http://localhost:$PORT${NC}"
echo -e "  📑 REST API Docs:         ${BOLD}http://localhost:$PORT/docs${NC}"
echo -e "  🔍 System Health:         ${BOLD}http://localhost:$PORT/health/ready${NC}"
echo -e "  📢 Official Updates:      ${BOLD}http://localhost:$PORT/api/v1/updates${NC}"
echo -e "  🏛️ Verified Schemes:     ${BOLD}http://localhost:$PORT/api/v1/schemes${NC}"
echo -e "${BLUE}================================================================${NC}\n"

if [ "$1" = "--daemon" ] || [ "$1" = "-d" ]; then
    nohup env PYTHONPATH=. "$PYTHON_BIN" -m uvicorn apps.api.main:app \
        --host "$HOST" \
        --port "$PORT" \
        --reload > "$PROJECT_ROOT/data/server.log" 2>&1 &
    SERVER_PID=$!
    echo "$SERVER_PID" > "$PID_FILE"
    echo -e "${GREEN}✓ Udyog Sathi running in background (PID: $SERVER_PID). Logs: data/server.log${NC}"
    exit 0
else
    # Save PID of foreground runner
    echo "$$" > "$PID_FILE"
    trap stop_server EXIT INT TERM
    export PYTHONPATH=.
    exec "$PYTHON_BIN" -m uvicorn apps.api.main:app \
        --host "$HOST" \
        --port "$PORT" \
        --reload
fi
