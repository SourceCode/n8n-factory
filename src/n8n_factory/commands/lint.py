import re
import sys
import json
from rich.console import Console
from ..models import Recipe
from ..assembler import WorkflowAssembler

console = Console()

def lint_recipe(recipe: Recipe, templates_dir: str, strict: bool = False, json_output: bool = False):
    if not json_output:
        console.print(f"Linting '[bold]{recipe.name}[/bold]' (strict={strict})...")
        
    errors = []
    warnings = []
    
    # 1. ID Naming
    snake_case = re.compile(r'^[a-z0-9_]+$')
    for step in recipe.steps:
        if not snake_case.match(step.id):
            warnings.append(f"Step ID '{step.id}' is not snake_case.")
            
    # 2. Description
    if not recipe.description:
        msg = "Recipe missing description."
        if strict: errors.append(msg)
        else: warnings.append(msg)
    
    # 3. Node Docs
    if strict:
        for step in recipe.steps:
            if not step.description and not step.notes:
                errors.append(f"Step '{step.id}' missing description or notes.")

    # 4. Assembly
    try:
        assembler = WorkflowAssembler(templates_dir)
        assembler.assemble(recipe)
    except Exception as e:
        errors.append(f"Assembly failed: {e}")
        
    result = {
        "recipe": recipe.name,
        "strict_mode": strict,
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "stats": {"error_count": len(errors), "warning_count": len(warnings)}
    }
    
    if json_output:
        print(json.dumps(result, indent=2))
        if strict and len(errors) > 0:
            sys.exit(1)
        return

    # Console Output
    for w in warnings:
        console.print(f"[yellow]Warning:[/yellow] {w}")
    for e in errors:
        console.print(f"[red]Error:[/red] {e}")
        
    if len(errors) == 0 and (len(warnings) == 0 or not strict):
        console.print("[bold green]Lint Passed! ✨[/bold green]")
    else:
        console.print(f"\n[bold]Summary:[/bold] {len(errors)} Errors, {len(warnings)} Warnings")
        if strict and len(errors) > 0:
            sys.exit(1)
