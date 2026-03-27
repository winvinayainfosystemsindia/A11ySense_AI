import os
import subprocess
import time
import sys
import signal
import json
from typing import Dict, List

SERVICES = {
    "gateway": {"port": 8000, "module": "src.services.gateway:app"},
    "crawler": {"port": 8001, "module": "src.services.crawler:app"},
    "analyzer": {"port": 8002, "module": "src.services.analyzer:app"},
    "llm": {"port": 8003, "module": "src.services.llm:app"},
    "reporting": {"port": 8004, "module": "src.services.reporting:app"},
}

PID_FILE = "storage/services.pid"

def get_pids() -> Dict[str, int]:
    if os.path.exists(PID_FILE):
        with open(PID_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_pids(pids: Dict[str, int]):
    os.makedirs(os.path.dirname(PID_FILE), exist_ok=True)
    with open(PID_FILE, "w") as f:
        json.dump(pids, f)

def start_services():
    pids = get_pids()
    new_pids = {}

    for name, config in SERVICES.items():
        if name in pids:
            # Check if process is still running
            try:
                os.kill(pids[name], 0)
                print(f"Service {name} is already running (PID {pids[name]})")
                new_pids[name] = pids[name]
                continue
            except OSError:
                print(f"Service {name} (PID {pids[name]}) not found. Restarting.")

        print(f"Starting {name} on port {config['port']}...")
        
        # Use venv if available, otherwise use sys.executable
        executable = sys.executable
        
        process = subprocess.Popen(
            [executable, "-m", "uvicorn", config['module'], "--port", str(config['port']), "--host", "127.0.0.1"],
            stdout=open(f"storage/logs/{name}.log", "a"),
            stderr=open(f"storage/logs/{name}.err", "a"),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        new_pids[name] = process.pid

    save_pids(new_pids)
    print("\nAll services started. PIDs saved to", PID_FILE)

def stop_services():
    pids = get_pids()
    if not pids:
        print("No services found in pid file.")
        return

    for name, pid in pids.items():
        print(f"Stopping {name} (PID {pid})...")
        try:
            if os.name == 'nt':
                os.kill(pid, signal.CTRL_BREAK_EVENT)
            else:
                os.kill(pid, signal.SIGTERM)
        except OSError:
            print(f"Service {name} (PID {pid}) not found.")

    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
    print("All services stopped.")

def status():
    pids = get_pids()
    if not pids:
        print("No services currently running according to PID file.")
        return

    print(f"{'Service':<15} | {'Port':<6} | {'PID':<8} | {'Status'}")
    print("-" * 45)
    for name, config in SERVICES.items():
        pid = pids.get(name)
        state = "STOPPED"
        if pid:
            try:
                os.kill(pid, 0)
                state = "RUNNING"
            except OSError:
                state = "ZOMBIE (Not found)"
        
        print(f"{name:<15} | {config['port']:<6} | {str(pid) if pid else 'N/A':<8} | {state}")

if __name__ == "__main__":
    os.makedirs("storage/logs", exist_ok=True)
    
    if len(sys.argv) < 2:
        print("Usage: python manager.py [start|stop|status]")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "start":
        start_services()
    elif cmd == "stop":
        stop_services()
    elif cmd == "status":
        status()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
