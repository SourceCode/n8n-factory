import os
import json
from rich.console import Console
from rich.table import Table

console = Console()

def search_templates(query: str, templates_dir: str = "templates"):
    console.print(f"Searching for '[bold cyan]{query}[/bold cyan]' in {templates_dir}...")
    
    table = Table(title="Search Results")
    table.add_column("Template", style="green")
    table.add_column("Match Context", style="yellow")
    
    files = [f for f in os.listdir(templates_dir) if f.endswith('.json')]
    found = False
    
    for filename in sorted(files):
        path = os.path.join(templates_dir, filename)
        name = filename.replace(".json", "")
        
        # Name match
        if query.lower() in name.lower():
            table.add_row(name, "Filename match")
            found = True
            continue
            
        # Content match
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                if query.lower() in content.lower():
                    # Extract snippet? 
                    # Simple heuristic: Just say content match
                    table.add_row(name, "Content match")
                    found = True
        except:
            pass
            
    if found:
        console.print(table)
    else:
        console.print("[dim]No matches found.[/dim]")
