import os
import requests
import json
from rich.console import Console
from ..models import Recipe
from ..assembler import WorkflowAssembler

console = Console()

def publish_workflow(recipe: Recipe, templates_dir: str, activate: bool = False):
    url = os.getenv("N8N_URL")
    api_key = os.getenv("N8N_API_KEY")
    
    if not url or not api_key:
        console.print("[bold red]Error:[/bold red] N8N_URL and N8N_API_KEY env vars must be set.")
        return

    console.print(f"Publishing '[bold]{recipe.name}[/bold]' to {url}...")
    
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
        "meta": workflow["meta"],
        "active": activate
    }
    
    try:
        # TODO: Check if workflow exists to update it instead of creating new?
        # Current logic creates new. N8N API POST /workflows creates. PUT /workflows/{id} updates.
        # To update, we need to know the ID. We don't store state mapping recipe->id yet.
        # So creating new is default behavior for factory (immutable infra style).
        
        resp = requests.post(endpoint, headers=headers, json=payload)
        resp.raise_for_status()
        res_data = resp.json()
        wf_id = res_data.get('id')
        console.print(f"[bold green]Success![/bold green] Workflow ID: {wf_id}")
        
        if activate:
            # POST endpoint activates if payload has active=True?
            # Yes, standard API supports it.
            if res_data.get('active'):
                console.print(f"[bold green]Workflow activated.[/bold green]")
            else:
                # If it failed to activate via POST, try activation endpoint
                act_resp = requests.post(f"{endpoint}/{wf_id}/activate", headers=headers)
                if act_resp.status_code == 200:
                    console.print(f"[bold green]Workflow activated manually.[/bold green]")
                
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]API Error:[/bold red] {e}")
        if e.response:
             console.print(f"Response: {e.response.text}")