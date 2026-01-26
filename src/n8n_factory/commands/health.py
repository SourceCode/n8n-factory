import sys
import shutil
import os
import json
from rich.console import Console

console = Console()

def health_command(json_output: bool = False):
    checks = {
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "docker_installed": shutil.which("docker") is not None,
        "templates_dir": os.path.isdir("templates"),
        "recipes_dir": os.path.isdir("recipes"),
        "config_file": os.path.exists(".n8n-factory.yaml"),
        "env_file": os.path.exists(".env")
    }
    
    healthy = checks["docker_installed"] and checks["templates_dir"]
    
    if json_output:
        print(json.dumps({"healthy": healthy, "checks": checks}, indent=2))
    else:
        console.print("[bold]System Health Check[/bold]")
        for k, v in checks.items():
            icon = "✅" if v else "❌"
            console.print(f"{icon} {k}: {v}")
        
        if healthy:
            console.print("[bold green]System is healthy.[/bold green]")
        else:
            console.print("[bold red]System has issues.[/bold red]")
