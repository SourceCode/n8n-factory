import os
import shutil
from rich.console import Console
from rich.table import Table

console = Console()

def examples_command(action: str = "list", name: str = None):
    examples_dir = "examples"
    if not os.path.exists(examples_dir):
        console.print("[red]No examples directory found.[/red]")
        return

    if action == "list":
        table = Table(title="Examples")
        table.add_column("Name", style="cyan")
        
        for f in os.listdir(examples_dir):
            if f.endswith(".yaml"):
                table.add_row(f)
        console.print(table)
        
    elif action == "copy":
        if not name:
            console.print("[red]Specify example name to copy.[/red]")
            return
        src = os.path.join(examples_dir, name)
        if not os.path.exists(src):
            console.print(f"[red]Example '{name}' not found.[/red]")
            return
        
        dst = name
        if os.path.exists(dst):
            console.print(f"[yellow]File '{dst}' already exists.[/yellow]")
            return
            
        shutil.copy(src, dst)
        console.print(f"[green]Copied {src} to {dst}[/green]")
