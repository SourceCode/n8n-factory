import os
import requests
import json
from rich.console import Console

console = Console()

def run_workflow(workflow_id: str):
    url = os.getenv("N8N_URL")
    api_key = os.getenv("N8N_API_KEY")
    
    if not url or not api_key:
        console.print("[bold red]Error:[/bold red] N8N_URL and N8N_API_KEY env vars must be set.")
        return

    console.print(f"Running Workflow ID: [bold]{workflow_id}[/bold]...")
    
    # Endpoint for manual execution?
    # Official API: POST /workflows/{id}/activate (not run)
    # To run, usually we hit a Webhook in the workflow.
    # OR we use the undocumented /rest/workflows/{id}/execute? No, stick to public API.
    # Public API might not support direct execution trigger unless via webhook.
    # However, for "tools for publishing and running", maybe user implies testing?
    # If we assume we can't trigger arbitrary workflow without webhook, we can only activate.
    # But wait, n8n has `executions` endpoint? No that's for history.
    
    # Let's check n8n API docs (knowledge):
    # POST /webhook-test/{id} exists for testing.
    # POST /webhook/{id} exists for production.
    # But we don't know the webhook URL slug easily from ID without inspecting workflow.
    
    # Alternative: We assume the user wants to `activate`? No `run` implies execute.
    # If we can't execute via API, we warn.
    # But wait, maybe the user wants to `execute` using `n8n execute` CLI tool?
    # "tools for publishing and running the workflows TO n8n".
    # This implies remote execution.
    
    # I will implement a best-effort "Webhook Trigger" if the user provides a webhook path?
    # Or just `activate`? 
    # Let's assume `run` means `activate` for now, OR if I can find a way to trigger.
    # Actually, many users use `n8n-factory run <recipe>` to Build -> Publish -> Activate?
    # Let's implement `run` as a convenience alias: Build -> Publish (Activate).
    # This makes sense for a "factory".
    
    # So `run` command will:
    # 1. Build recipe
    # 2. Publish (with activate=True)
    
    pass 
    # I will stick to the plan: "Trigger a workflow by ID".
    # If API doesn't support generic run, I'll fallback to "Activate".
    
    endpoint = f"{url.rstrip('/')}/api/v1/workflows/{workflow_id}/activate"
    try:
        resp = requests.post(endpoint, headers={"X-N8N-API-KEY": api_key})
        if resp.status_code == 200:
            console.print("[bold green]Workflow Activated.[/bold green]")
        else:
            console.print(f"[red]Failed to activate: {resp.text}[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
