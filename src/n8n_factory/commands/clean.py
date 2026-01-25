import os
import glob
from rich.console import Console

console = Console()

def clean_command():
    console.print("[bold]Cleaning generated files...[/bold]")
    
    # Remove json files that look like workflows
    # Be careful not to delete templates!
    # Heuristic: delete .json files in root, or specific output folder.
    # Safe approach: delete specific patterns or ask user.
    # For this tool, we'll delete *.json in current dir EXCLUDING package.json or similar common ones if they exist.
    
    files = glob.glob("*.json")
    deleted = 0
    for f in files:
        if f in ["package.json", "tsconfig.json", "recipe.schema.json"]:
            continue
        try:
            os.remove(f)
            console.print(f"[dim]Deleted {f}[/dim]")
            deleted += 1
        except Exception as e:
            console.print(f"[red]Failed to delete {f}: {e}[/red]")
            
    # Clean pycache
    # ... (skipping recursive pycache clean for safety/complexity in simple script)
    
    console.print(f"[green]Cleaned {deleted} files.[/green]")
