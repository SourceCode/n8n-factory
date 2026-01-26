import os
import glob
import json
from rich.console import Console

console = Console()

IGNORED_FILES = [
    "package.json", 
    "tsconfig.json", 
    "recipe.schema.json",
    "pyproject.toml" # Just in case glob logic changes
]

def clean_command(json_output: bool = False):
    if not json_output:
        console.print("[bold]Cleaning generated files...[/bold]")
    
    files = glob.glob("*.json")
    deleted_files = []
    errors = []
    
    for f in files:
        if f in IGNORED_FILES:
            continue
        try:
            os.remove(f)
            deleted_files.append(f)
            if not json_output:
                console.print(f"[dim]Deleted {f}[/dim]")
        except Exception as e:
            errors.append(f"{f}: {str(e)}")
            if not json_output:
                console.print(f"[red]Failed to delete {f}: {e}[/red]")
            
    if json_output:
        print(json.dumps({
            "deleted": deleted_files,
            "errors": errors,
            "count": len(deleted_files)
        }, indent=2))
    else:
        console.print(f"[green]Cleaned {len(deleted_files)} files.[/green]")