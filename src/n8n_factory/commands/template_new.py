import os
import json
from rich.console import Console
from rich.prompt import Prompt, Confirm

console = Console()

def template_new_command(output_dir: str = "templates", name: str = None, node_type: str = None, json_output: bool = False):
    if not json_output:
        console.print("[bold blue]Create New Template[/bold blue]")
    
    if not name:
        if json_output:
            print(json.dumps({"error": "Name required in JSON mode"}))
            return
        name = Prompt.ask("Template Name (file basename)", default="my_node")
    
    if not node_type:
        if json_output:
            # Default or error? Let's default.
            node_type = "n8n-nodes-base.httpRequest"
        else:
            node_type = Prompt.ask("n8n Node Type", default="n8n-nodes-base.httpRequest")
    
    params = {}
    if not json_output:
        while True:
            if not Confirm.ask("Add a parameter?"):
                break
            key = Prompt.ask("Param Key (e.g. url)")
            default = Prompt.ask("Default Value (optional)")
            
            if default:
                val = f"{{{{ {key} | default('{default}') }}}}"
            else:
                val = f"{{{{ {key} }}}}"
                
            params[key] = val
        
    template = {
        "_meta": {
            "required_params": list(params.keys()),
            "param_types": {k: "string" for k in params.keys()}
        },
        "parameters": params,
        "type": node_type,
        "typeVersion": 1,
        "position": [0, 0]
    }
    
    path = os.path.join(output_dir, f"{name}.json")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    with open(path, "w") as f:
        json.dump(template, f, indent=2)
        
    if json_output:
        print(json.dumps({"status": "created", "path": path}))
    else:
        console.print(f"[bold green]Template created:[/bold green] {path}")