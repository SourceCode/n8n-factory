import os
import json
from rich.console import Console
from rich.syntax import Syntax

console = Console()

def inspect_template(template_name: str, templates_dir: str = "templates"):
    path = os.path.join(templates_dir, f"{template_name}.json")
    if not os.path.exists(path):
        console.print(f"[bold red]Error:[/bold red] Template '{template_name}' not found.")
        return

    console.print(f"[bold blue]Inspecting Template:[/bold blue] {template_name}")
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    try:
        data = json.loads(content)
        meta = data.get("_meta", {})
        console.print(f"Type: [green]{data.get('type')}[/green]")
        if meta:
            console.print("Meta Info:", meta)
    except:
        console.print("[yellow]Warning: Invalid JSON or contains Jinja syntax preventing parse[/yellow]")

    console.print("\n[bold]Raw Content:[/bold]")
    syntax = Syntax(content, "json", theme="monokai", line_numbers=True)
    console.print(syntax)

