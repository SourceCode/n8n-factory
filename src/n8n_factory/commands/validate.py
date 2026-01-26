from rich.console import Console
from ..models import Recipe
from ..assembler import WorkflowAssembler
import re
import os
import json

console = Console()

def validate_recipe(recipe: Recipe, templates_dir: str, check_env: bool = False, check_js: bool = False, json_output: bool = False):
    if not json_output:
        console.print(f"Validating '[bold]{recipe.name}[/bold]'...")
    
    validation_result = {
        "recipe": recipe.name,
        "valid": False,
        "checks": {}
    }
    
    # Assembly Check
    try:
        assembler = WorkflowAssembler(templates_dir)
        assembler.assemble(recipe)
        validation_result["checks"]["assembly"] = {
            "status": "passed",
            "steps": len(recipe.steps)
        }
        validation_result["valid"] = True
    except Exception as e:
        validation_result["checks"]["assembly"] = {
            "status": "failed",
            "error": str(e)
        }
        if json_output:
            print(json.dumps(validation_result, indent=2))
        else:
            console.print(f"[bold red]Validation Failed:[/bold red] {e}")
        return

    # Env Check
    if check_env:
        pattern = re.compile(r'\$env\.([a-zA-Z0-9_]+)')
        pattern_bracket = re.compile(r'\$env\[["\"]([a-zA-Z0-9_]+)["\"]\]')
        env_vars_found = set()
        
        for step in recipe.steps:
            for k, v in step.params.items():
                s_val = str(v)
                for m in pattern.findall(s_val): env_vars_found.add(m)
                for m in pattern_bracket.findall(s_val): env_vars_found.add(m)
        
        missing = [v for v in env_vars_found if v not in os.environ]
        
        validation_result["checks"]["environment"] = {
            "referenced": list(env_vars_found),
            "missing": missing,
            "status": "passed" if not missing else "warning" 
        }
        
        if not json_output and missing:
             console.print(f"[bold red]Missing Env Vars:[/bold red] {', '.join(missing)}")

    # JS Check
    if check_js:
        js_issues = []
        for step in recipe.steps:
            code = ""
            if step.template == "code":
                code = step.params.get("code") or step.params.get("jsCode", "")
            elif "js" in step.params: # some templates accept JS
                pass # harder to detect which param
            
            if code:
                # Heuristic: Balance check
                if code.count("{") != code.count("}"):
                    js_issues.append(f"Step {step.id}: Unbalanced braces {{}}")
                if code.count("(") != code.count(")"):
                    js_issues.append(f"Step {step.id}: Unbalanced parentheses ()")
        
        validation_result["checks"]["javascript"] = {
            "issues": js_issues,
            "status": "passed" if not js_issues else "warning"
        }
        if not json_output and js_issues:
            console.print("[bold yellow]JS Warnings:[/bold yellow]")
            for i in js_issues: console.print(f"- {i}")

    if json_output:
        print(json.dumps(validation_result, indent=2))
    elif validation_result["valid"]:
        console.print("[bold green]Validation Passed![/bold green]")