import sys
import os
import requests
import yaml
from rich.console import Console
from dotenv import load_dotenv

console = Console()
load_dotenv()

def doctor_command():
    console.print("[bold blue]n8n Factory Doctor[/bold blue]")
    
    # Check Python
    py_ver = sys.version.split(" ")[0]
    console.print(f"[green]✓[/green] Python Version: {py_ver}")
    
    # Check .env
    if os.path.exists(".env"):
        console.print("[green]✓[/green] .env file found")
    else:
        console.print("[yellow]![/yellow] .env file missing")

    # Check n8n connection
    url = os.getenv("N8N_URL")
    api_key = os.getenv("N8N_API_KEY")
    
    if url and api_key:
        try:
            # Simple health check or user info
            endpoint = f"{url.rstrip('/')}/api/v1/users/me"
            headers = {"X-N8N-API-KEY": api_key}
            resp = requests.get(endpoint, headers=headers, timeout=5)
            if resp.status_code == 200:
                console.print(f"[green]✓[/green] n8n Connection OK ({url})")
            else:
                 console.print(f"[red]x[/red] n8n Connection Failed: {resp.status_code}")
        except Exception as e:
            console.print(f"[red]x[/red] n8n Connection Error: {e}")
    else:
        console.print("[yellow]![/yellow] N8N_URL or N8N_API_KEY not set in environment")

    # Check templates
    if os.path.exists("templates"):
        count = len([f for f in os.listdir("templates") if f.endswith(".json")])
        console.print(f"[green]✓[/green] Templates directory found ({count} templates)")
    else:
        console.print("[red]x[/red] Templates directory 'templates/' missing")
