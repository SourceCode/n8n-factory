import os
import json
from rich.console import Console
from rich.table import Table

console = Console()

COMMON_PATTERNS = {
    "aws": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "openai": ["OPENAI_API_KEY"],
    "slack": ["SLACK_BOT_TOKEN"],
    "postgres": ["POSTGRES_USER", "POSTGRES_PASSWORD", "DB_POSTGRESDB_PASSWORD"],
    "n8n": ["N8N_BASIC_AUTH_PASSWORD", "N8N_ENCRYPTION_KEY"],
    "redis": ["REDIS_PASSWORD"]
}

def creds_command(scaffold: bool = False, json_output: bool = False):
    if scaffold:
        if not os.path.exists(".env.example"):
            with open(".env.example", "w") as f:
                for service, vars in COMMON_PATTERNS.items():
                    f.write(f"# {service.upper()}\n")
                    for v in vars:
                        f.write(f"{v}=\n")
                    f.write("\n")
            msg = "Created .env.example with common credentials."
        else:
            msg = ".env.example already exists."
            
        if json_output:
            print(json.dumps({"status": "scaffolded", "message": msg}))
        else:
            console.print(f"[green]{msg}[/green]")
        return

    found = {}
    for service, vars in COMMON_PATTERNS.items():
        present = [v for v in vars if v in os.environ]
        if len(present) == len(vars):
            found[service] = "Available"
        elif present:
            found[service] = "Partial"
        else:
            found[service] = "Missing"
    
    if json_output:
        print(json.dumps(found, indent=2))
        return

    table = Table(title="Credential Environment Check")
    table.add_column("Service", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Variables", style="dim")
    
    for s, status in found.items():
        color = "green" if status == "Available" else "yellow" if status == "Partial" else "red"
        table.add_row(s, f"[{color}]{status}[/{color}]", ", ".join(COMMON_PATTERNS[s]))
    
    console.print(table)