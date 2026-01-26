import json
import yaml
import os
from rich.console import Console

console = Console()

def import_command(input_file: str, output_file: str = None, json_output: bool = False):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
    except Exception as e:
        if json_output:
            print(json.dumps({"error": f"Failed to load input file: {e}"}))
        else:
            console.print(f"[red]Failed to load input file: {e}[/red]")
        return
        
    name = workflow.get("name", "Imported Workflow")
    nodes = workflow.get("nodes", [])
    
    steps = []
    for node in nodes:
        # Use 'raw' template for maximum compatibility
        step = {
            "id": node.get("name"),
            "template": "raw",
            "params": {
                "type": node.get("type"),
                "typeVersion": node.get("typeVersion", 1),
                "position": node.get("position", [0, 0]),
                "parameters": node.get("parameters", {})
            },
            "notes": node.get("notes")
        }
        steps.append(step)
        
    # Map connections
    connections = workflow.get("connections", {})
    
    for step in steps:
        step_id = step["id"]
        sources = []
        for src_node, outputs in connections.items():
            for output_type, links in outputs.items():
                for link in links:
                    for item in link:
                        if item["node"] == step_id:
                            # We found a connection TO this node
                            # We should record it.
                            # assembler expects 'connections_from'
                            # If connection is standard 'main', just src_node string
                            # If complex, need Connection object.
                            # For MVP import, assume 'main' or string.
                            sources.append(src_node)
        
        if sources:
            # unique sources
            step["connections_from"] = list(set(sources))

    recipe = {
        "name": name,
        "steps": steps
    }
    
    if not output_file:
        if not os.path.exists("recipes"):
            os.makedirs("recipes")
        safe_name = "".join([c if c.isalnum() else "_" for c in name]).lower()
        output_file = f"recipes/{safe_name}.yaml"
        
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(recipe, f, sort_keys=False)
            
        if json_output:
            print(json.dumps({"status": "imported", "recipe": output_file}, indent=2))
        else:
            console.print(f"[bold green]Imported workflow to:[/bold green] {output_file}")
            
    except Exception as e:
        if json_output:
            print(json.dumps({"error": f"Failed to save recipe: {e}"}))
        else:
            console.print(f"[red]Failed to save recipe: {e}[/red]")
