import json
import os
import time
import uuid
from functools import wraps
from typing import Dict, Any

TELEMETRY_FILE = ".n8n-factory-telemetry.json"

def load_telemetry() -> list:
    if os.path.exists(TELEMETRY_FILE):
        try:
            with open(TELEMETRY_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return []

def save_telemetry(events: list):
    # Keep last 1000 events
    if len(events) > 1000:
        events = events[-1000:]
    with open(TELEMETRY_FILE, 'w') as f:
        json.dump(events, f, indent=2)

def log_event(command: str, params: Dict[str, Any], status: str, duration: float, error: str = None):
    event = {
        "id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "command": command,
        "params": {k: str(v) for k, v in params.items() if k != "json"}, # exclude common flags like json
        "status": status,
        "duration": duration,
        "error": error
    }
    events = load_telemetry()
    events.append(event)
    save_telemetry(events)

def track_command(cmd_name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            status = "success"
            error = None
            try:
                return func(*args, **kwargs)
            except Exception as e:
                status = "error"
                error = str(e)
                raise
            finally:
                duration = time.time() - start
                # Convert args/kwargs to dict for logging
                params = {}
                # This is a bit rough for generic functions, but mostly for CLI handlers it's fine
                if kwargs:
                    params.update(kwargs)
                log_event(cmd_name, params, status, duration, error)
        return wrapper
    return decorator
