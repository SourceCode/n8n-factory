import os
import json
from rich.console import Console
from rich.table import Table

console = Console()

def search_templates(query: str, templates_dir: str = "templates", json_output: bool = False):
    if not json_output:
        console.print(f"Searching for '[bold cyan]{query}[/bold cyan]' in {templates_dir}...")
        table = Table(title="Search Results")
        table.add_column("Template", style="green")
        table.add_column("Match Context", style="yellow")
    
    files = [f for f in os.listdir(templates_dir) if f.endswith('.json')]
    results = []
    
    for filename in sorted(files):
        path = os.path.join(templates_dir, filename)
        name = filename.replace(".json", "")
        match_type = None
        
        # Name match
        if query.lower() in name.lower():
            match_type = "Filename match"
        
        # Content match
        if not match_type:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if query.lower() in content.lower():
                        match_type = "Content match"
            except:
                pass
        
        if match_type:
            results.append({"name": name, "match": match_type})
            if not json_output:
                table.add_row(name, match_type)

    if json_output:
        print(json.dumps(results, indent=2))
    elif results:
        console.print(table)
    else:
        console.print("[dim]No matches found.[/dim]")