import re
import json
from rich.console import Console
from ..models import Recipe

console = Console()

def security_command(recipe: Recipe, strict: bool = False, json_output: bool = False):
    patterns = [
        (r'(api_?key|token|secret|password|passwd)', "Potential Secret Key in Param Name/Value"),
        (r'sk-[a-zA-Z0-9]{20,}', "OpenAI/Stripe Key format"),
        (r'xox[baprs]-([0-9a-zA-Z]{10,48})', "Slack Token"),
        (r'-----BEGIN (RSA|DSA|EC|PGP|OPENSSH) PRIVATE KEY', "Private Key Block")
    ]
    
    issues = []
    
    for step in recipe.steps:
        for k, v in step.params.items():
            val_str = str(v)
            # Simple check: ignore keys, focus on value leaks or suspicious key names with hardcoded values
            
            is_env = "${" in val_str or "$env." in val_str or "=$env" in val_str
            
            for pat, desc in patterns:
                # Check key name matches 'password' AND value is NOT env var
                if re.search(pat, k, re.IGNORECASE):
                     if not is_env and len(val_str) > 0:
                         issues.append({"step": step.id, "param": k, "issue": desc, "context": "key match, value literal"})
                
                # Check value matches a secret pattern (e.g. sk-...)
                if re.search(pat, val_str): # Case sensitive for values usually
                     if not is_env:
                         issues.append({"step": step.id, "param": k, "issue": desc, "context": "value match"})

    if json_output:
        print(json.dumps({"status": "failed" if issues else "passed", "issues": issues}, indent=2))
        return

    if not issues:
        console.print("[bold green]Security Audit Passed.[/bold green]")
    else:
        console.print(f"[bold red]Security Issues Found ({len(issues)}):[/bold red]")
        for i in issues:
            console.print(f"- Step [cyan]{i['step']}[/cyan]: {i['issue']} in {i['context']} ('{i['param']}')")
