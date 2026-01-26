import os
import yaml
import json
from rich.console import Console

console = Console()

def config_command(json_output: bool = False):
    config = {}
    config_path = ".n8n-factory.yaml"
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
        except Exception as e:
            if json_output:
                print(json.dumps({"error": str(e)}))
                return
            console.print(f"[red]Error loading config: {e}[/red]")
            return
            
    # Merge with defaults
    defaults = {
        "templates_dir": "templates",
        "default_tags": [],
        "n8n_url": "http://localhost:5678"
    }
    
    final_config = {**defaults, **config}
    
    if json_output:
        print(json.dumps(final_config, indent=2))
    else:
        console.print("[bold]Current Configuration:[/bold]")
        console.print(yaml.dump(final_config, sort_keys=False))
