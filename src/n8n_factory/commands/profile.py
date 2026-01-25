import os
import shutil
from rich.console import Console

console = Console()

def profile_command(profile_name: str):
    target = f".env.{profile_name}"
    if not os.path.exists(target):
        console.print(f"[bold red]Error:[/bold red] Profile file '{target}' not found.")
        return
        
    console.print(f"Switching to profile: [bold]{profile_name}[/bold]")
    
    # Copy file to .env
    try:
        shutil.copy(target, ".env")
        console.print(f"[green]✓[/green] Updated .env from {target}")
    except Exception as e:
        console.print(f"[bold red]Failed:[/bold red] {e}")
