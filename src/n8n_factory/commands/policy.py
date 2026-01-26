import yaml
import os
import re
import json
from rich.console import Console
from ..models import Recipe

console = Console()

def policy_check_command(recipe: Recipe, policy_path: str = "policy.yaml", json_output: bool = False):
    if not os.path.exists(policy_path):
        if json_output:
            print(json.dumps({"status": "skipped", "reason": "No policy.yaml found"}))
        else:
            console.print("[dim]No policy.yaml found. Skipping policy check.[/dim]")
        return True

    with open(policy_path, 'r') as f:
        policy = yaml.safe_load(f) or {}

    violations = []

    # 1. Allowed Nodes
    allowed = set(policy.get("allowed_nodes", []))
    forbidden = set(policy.get("forbidden_nodes", []))
    
    for step in recipe.steps:
        # Check forbidden (higher priority)
        if step.template in forbidden:
            violations.append(f"Step '{step.id}' uses forbidden template '{step.template}'")
        
        # Check allowed (whitelist mode)
        if allowed and step.template not in allowed:
            violations.append(f"Step '{step.id}' uses unauthorized template '{step.template}'")

    # 2. Naming Convention
    naming_pattern = policy.get("naming_convention")
    if naming_pattern:
        regex = re.compile(naming_pattern)
        for step in recipe.steps:
            if not regex.match(step.id):
                violations.append(f"Step ID '{step.id}' does not match naming convention '{naming_pattern}'")

    # 3. Required Settings (e.g. retry)
    req_settings = policy.get("required_settings", {})
    if req_settings.get("retryOnFail") is True:
        for step in recipe.steps:
            # Only checking HTTP or flaky nodes? Or all?
            # For now, check if 'retry' config is present if the policy demands it generally.
            # This is hard to enforce generically on Recipe object which has 'retry' optional.
            if not step.retry:
                 # Check if template is usually flaky?
                 if "http" in step.template or "api" in step.template:
                     violations.append(f"Step '{step.id}' ({step.template}) requires retry configuration.")

    result = {
        "policy_file": policy_path,
        "violations": violations,
        "passed": len(violations) == 0
    }

    if json_output:
        print(json.dumps(result, indent=2))
    else:
        if violations:
            console.print(f"[bold red]Policy Violations Found ({len(violations)}):[/bold red]")
            for v in violations:
                console.print(f"- {v}")
        else:
            console.print("[bold green]Policy Check Passed.[/bold green]")
            
    return len(violations) == 0
