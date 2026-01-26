import os
import json
from rich.console import Console
from rich.syntax import Syntax

console = Console()

def inspect_template(template_name: str, templates_dir: str = "templates", json_output: bool = False):
    path = os.path.join(templates_dir, f"{template_name}.json")
    if not os.path.exists(path):
        if json_output:
            print(json.dumps({"error": f"Template '{template_name}' not found."}))
        else:
            console.print(f"[bold red]Error:[/bold red] Template '{template_name}' not found.")
        return

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    try:
        data = json.loads(content)
    except:
        data = None # Raw content might be invalid JSON due to Jinja
        
    if json_output:
        # Return structured info even if raw is mixed
        result = {
            "name": template_name,
            "path": path,
            "raw": content,
            "parsed": data
        }
        print(json.dumps(result, indent=2))
        return

    console.print(f"[bold blue]Inspecting Template:[/bold blue] {template_name}")
    if data:
        meta = data.get("_meta", {})
        console.print(f"Type: [green]{data.get('type')}[/green]")
        if meta:
            console.print("Meta Info:", meta)
    else:
        console.print("[yellow]Warning: Invalid JSON or contains Jinja syntax preventing parse[/yellow]")

    console.print("\n[bold]Raw Content:[/bold]")
    syntax = Syntax(content, "json", theme="monokai", line_numbers=True)
    console.print(syntax)