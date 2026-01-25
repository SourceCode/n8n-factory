import os
import json
from rich.console import Console
from rich.table import Table

def list_templates(templates_dir: str = "templates", json_output: bool = False):
    console = Console()
    
    if not os.path.exists(templates_dir):
        console.print(f"[bold red]Error:[/bold red] Templates directory '{templates_dir}' not found.")
        return

    files = [f for f in os.listdir(templates_dir) if f.endswith('.json')]
    results = []
    
    for filename in sorted(files):
        name = filename.replace('.json', '')
        path = os.path.join(templates_dir, filename)
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            node_type = data.get("type", "unknown")
            import re
            content = json.dumps(data)
            params = set(re.findall(r'\{\{\s*([a-zA-Z0-9_]+)', content))
            
            results.append({
                "name": name,
                "type": node_type,
                "params": list(params)
            })
            
        except Exception:
            results.append({"name": name, "error": "Parse Error"})

    if json_output:
        print(json.dumps(results, indent=2))
    else:
        table = Table(title="Available Templates")
        table.add_column("Template Name", style="cyan", no_wrap=True)
        table.add_column("Type", style="magenta")
        table.add_column("Parameters", style="green")
        
        for r in results:
            if "error" in r:
                table.add_row(r["name"], "Error", "")
            else:
                table.add_row(r["name"], r["type"], ", ".join(sorted(r["params"])))
        console.print(table)