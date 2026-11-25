#!/usr/bin/env bash
# Kali MCP Server Control Script
PORT=5000
IP="127.0.0.1"
LOG_FILE="/tmp/kali-server-mcp.log"
PID_FILE="/tmp/kali-server-mcp.pid"

start_server() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "[!] kali-server-mcp is already running (PID: $(cat "$PID_FILE"))."
        return 0
    fi

    echo "[*] Starting kali-server-mcp on ${IP}:${PORT}..."
    nohup /usr/bin/kali-server-mcp --ip "$IP" --port "$PORT" > "$LOG_FILE" 2>&1 &
    local pid=$!
    echo "$pid" > "$PID_FILE"

    # Wait for server to be responsive
    sleep 2
    if kill -0 "$pid" 2>/dev/null; then
        echo "[+] kali-server-mcp started successfully (PID: $pid)!"
        echo "[*] Logs: $LOG_FILE"
        python3 -c "
import requests
s = requests.Session()
s.trust_env = False
try:
    r = s.get('http://${IP}:${PORT}/health', timeout=3)
    if r.status_code == 200:
        print('[+] Health check passed:', r.json().get('status', 'OK'))
    else:
        print('[-] Unexpected response:', r.status_code)
except Exception as e:
    print('[-] Health check error:', e)
"
    else
        echo "[-] Failed to start kali-server-mcp. Check $LOG_FILE for details."
        rm -f "$PID_FILE"
        return 1
    fi
}

stop_server() {
    if [ -f "$PID_FILE" ]; then
        local pid
        pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            echo "[*] Stopping kali-server-mcp (PID: $pid)..."
            kill "$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null
            rm -f "$PID_FILE"
            echo "[+] Stopped."
        else
            echo "[!] PID file found but process $pid is not running."
            rm -f "$PID_FILE"
        fi
    else
        # Try killing by name
        pkill -f "kali-server-mcp" 2>/dev/null && echo "[+] Process terminated." || echo "[!] Not running."
    fi
}

status_server() {
    python3 -c "
import requests
s = requests.Session()
s.trust_env = False
try:
    r = s.get('http://${IP}:${PORT}/health', timeout=2)
    if r.status_code == 200:
        print('[+] kali-server-mcp is RUNNING and healthy on http://${IP}:${PORT}')
        data = r.json()
        print('    Available tools:', data.get('tools_status', {}))
    else:
        print('[-] Server responded with status code:', r.status_code)
except Exception:
    print('[-] kali-server-mcp is NOT running on http://${IP}:${PORT}')
"
}

case "$1" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        stop_server
        sleep 1
        start_server
        ;;
    status)
        status_server
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
