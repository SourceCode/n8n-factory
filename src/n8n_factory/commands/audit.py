import json
from rich.console import Console
from ..utils import load_recipe

console = Console()

def audit_command(recipe_path: str, json_output: bool = False):
    recipe = load_recipe(recipe_path)
    issues = []
    
    for step in recipe.steps:
        # HTTP Check
        if "http" in step.template.lower() or "request" in step.template.lower():
            if "timeout" not in step.params and "options" not in step.params:
                 issues.append({"step": step.id, "severity": "medium", "msg": "HTTP node missing explicit timeout config"})
        
        # Webhook Check
        if "webhook" in step.template.lower():
            auth = step.params.get("authentication")
            if not auth or auth == "none":
                 issues.append({"step": step.id, "severity": "high", "msg": "Webhook has no authentication configured"})

    if json_output:
        print(json.dumps({"issues": issues, "score": 100 - (len(issues)*10)}, indent=2))
    else:
        if issues:
            console.print(f"[bold red]Audit Issues ({len(issues)}):[/bold red]")
            for i in issues:
                console.print(f"- [{i['severity'].upper()}] {i['step']}: {i['msg']}")
        else:
            console.print("[bold green]Audit Passed.[/bold green]")
