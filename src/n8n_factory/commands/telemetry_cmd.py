import json
from ..telemetry import load_telemetry

def telemetry_export_command(json_output: bool = True):
    events = load_telemetry()
    print(json.dumps(events, indent=2))
