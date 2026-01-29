import os
import requests
import json
from rich.console import Console
from ..models import Recipe
from ..assembler import WorkflowAssembler

console = Console()

def publish_workflow(recipe: Recipe, templates_dir: str, activate: bool = False, json_output: bool = False):
    url = os.getenv("N8N_URL")
    api_key = os.getenv("N8N_API_KEY")
    
    if not url or not api_key:
        err = "N8N_URL and N8N_API_KEY env vars must be set."
        if json_output:
            print(json.dumps({"error": err}))
        else:
            console.print(f"[bold red]Error:[/bold red] {err}")
        return

    if not json_output:
        console.print(f"Publishing '[bold]{recipe.name}[/bold]' to {url}...")
    
    try:
        assembler = WorkflowAssembler(templates_dir)
        workflow = assembler.assemble(recipe)
        
        endpoint = f"{url.rstrip('/')}/api/v1/workflows"
        headers = {
            "X-N8N-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "name": workflow["name"],
            "nodes": workflow["nodes"],
            "connections": workflow["connections"],
            "settings": workflow.get("settings", {}),
            "active": activate
        }
    
        resp = requests.post(endpoint, headers=headers, json=payload)
        resp.raise_for_status()
        res_data = resp.json()
        wf_id = res_data.get('id')
        active_status = res_data.get('active', False)
        
        if activate and not active_status:
             # Try explicit activation if creation didn't do it
             try:
                 act_resp = requests.post(f"{endpoint}/{wf_id}/activate", headers=headers)
                 if act_resp.status_code == 200:
                     active_status = True
             except:
                 pass

        if json_output:
            print(json.dumps({
                "status": "published",
                "id": wf_id,
                "name": workflow["name"],
                "active": active_status,
                "api_response": res_data
            }, indent=2))
        else:
            console.print(f"[bold green]Success![/bold green] Workflow ID: {wf_id}")
            if active_status:
                console.print(f"[bold green]Workflow activated.[/bold green]")
                
    except Exception as e:
        err_msg = str(e)
        if isinstance(e, requests.exceptions.RequestException) and e.response:
             err_msg += f" Response: {e.response.text}"
             
        if json_output:
            print(json.dumps({"error": err_msg}))
        else:
            console.print(f"[bold red]API Error:[/bold red] {err_msg}")
