import os
import yaml
import json
from rich.console import Console
from rich.prompt import Prompt, Confirm

console = Console()

def init_recipe(minimal: bool = False, json_output: bool = False):
    if not minimal and not json_output:
        console.print("[bold blue]n8n Factory - Recipe Wizard[/bold blue]")
    
    if minimal:
        name = "Minimal Workflow"
        desc = "A minimal example"
        steps = [{
            "id": "start",
            "template": "webhook",
            "params": {"path": "test", "method": "GET"}
        }]
    else:
        name = Prompt.ask("Workflow Name", default="My New Workflow")
        desc = Prompt.ask("Description", default="A workflow created by n8n-factory")
        
        steps = []
        
        # Add Trigger
        if Confirm.ask("Add a Webhook Trigger?"):
            path = Prompt.ask("Webhook Path", default="my-hook")
            steps.append({
                "id": "trigger",
                "template": "webhook",
                "params": {"path": path, "method": "POST"}
            })
            
        # Add more steps
        while True:
            if not Confirm.ask("Add another step?"):
                break
                
            step_id = Prompt.ask("Step ID")
            template = Prompt.ask("Template Name", default="set")
            
            # Simple param parser
            console.print("[dim]Enter params as key=value (comma separated) or skip[/dim]")
            params_str = Prompt.ask("Parameters")
            params = {}
            if params_str:
                for pair in params_str.split(","):
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        params[k.strip()] = v.strip()
                        
            steps.append({
                "id": step_id,
                "template": template,
                "params": params
            })
        
    recipe = {
        "name": name,
        "description": desc,
        "steps": steps
    }
    
    filename = name.lower().replace(" ", "_") + ".yaml"
    if not os.path.exists("recipes"):
        os.makedirs("recipes")
    
    path = os.path.join("recipes", filename)
    
    with open(path, "w") as f:
        yaml.dump(recipe, f, sort_keys=False)
        
    if json_output:
        print(json.dumps({"status": "created", "path": path}, indent=2))
    else:
        console.print(f"[bold green]Recipe created:[/bold green] {path}")