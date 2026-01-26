import json
import os
from rich.console import Console

console = Console()

def template_extract_command(workflow_file: str, node_name: str, output_dir: str = "templates", json_output: bool = False):
    if not os.path.exists(workflow_file):
        err = f"Workflow file not found: {workflow_file}"
        if json_output: print(json.dumps({"error": err})); return
        else: console.print(f"[red]{err}[/red]"); return

    with open(workflow_file, 'r', encoding='utf-8') as f:
        wf = json.load(f)
        
    target_node = next((n for n in wf.get("nodes", []) if n.get("name") == node_name), None)
    
    if not target_node:
        err = f"Node '{node_name}' not found in workflow."
        if json_output: print(json.dumps({"error": err})); return
        else: console.print(f"[red]{err}[/red]"); return

    params = target_node.get("parameters", {})
    template_params = {}
    
    # Auto-parameterize top-level keys
    for k, v in params.items():
        if isinstance(v, str) and len(v) < 100: # Heuristic: don't parameterize huge scripts automatically
            # Escape existing braces?
            safe_v = v.replace("{{", "").replace("}}", "")
            template_params[k] = f"{{{{ {k} | default('{safe_v}') }}}}"
        else:
            template_params[k] = v
            
    template = {
        "_meta": {
            "description": f"Extracted from {os.path.basename(workflow_file)} (Node: {node_name})",
            "required_params": [k for k,v in params.items() if isinstance(v, str) and len(v)<100]
        },
        "parameters": template_params,
        "type": target_node.get("type"),
        "typeVersion": target_node.get("typeVersion", 1),
        "position": [0, 0]
    }
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Sanitize filename
    safe_name = "".join([c if c.isalnum() else "_" for c in node_name]).lower()
    out_path = os.path.join(output_dir, f"{safe_name}.json")
    
    with open(out_path, 'w') as f:
        json.dump(template, f, indent=2)
        
    if json_output:
        print(json.dumps({"status": "extracted", "path": out_path}))
    else:
        console.print(f"[bold green]Template extracted to:[/bold green] {out_path}")
