import os
import json
from rich.console import Console

console = Console()

def project_init_command(force: bool = False, json_output: bool = False):
    dirs = ["recipes", "templates", "tests", "config", "backups", "logs"]
    files = {
        ".gitignore": "*.json\n.env\n__pycache__/\nlogs/\nbackups/*.pyc",
        ".env.example": "N8N_URL=http://localhost:5678\nN8N_API_KEY="
    }
    
    created = []
    
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d)
            created.append(f"{d}/")
            
    for name, content in files.items():
        if not os.path.exists(name) or force:
            with open(name, "w") as f:
                f.write(content)
            created.append(name)
            
    if json_output:
        print(json.dumps({"created": created, "status": "initialized"}, indent=2))
    else:
        if created:
            console.print(f"[green]Initialized project:[/green] {', '.join(created)}")
        else:
            console.print("[yellow]Project already initialized.[/yellow]")
