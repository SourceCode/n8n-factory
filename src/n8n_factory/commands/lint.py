import re
from rich.console import Console
from ..models import Recipe
from ..assembler import WorkflowAssembler

console = Console()

def lint_recipe(recipe: Recipe, templates_dir: str):
    console.print(f"Linting '[bold]{recipe.name}[/bold]'...")
    errors = 0
    warnings = 0
    
    # 1. ID Naming Convention (snake_case)
    snake_case = re.compile(r'^[a-z0-9_]+$')
    for step in recipe.steps:
        if not snake_case.match(step.id):
            console.print(f"[yellow]Warning:[/yellow] Step ID '{step.id}' is not snake_case.")
            warnings += 1
            
    # 2. Description Check
    if not recipe.description:
        console.print("[yellow]Warning:[/yellow] Recipe missing description.")
        warnings += 1
        
    # 3. Dry Run Assembly (Check connections)
    try:
        assembler = WorkflowAssembler(templates_dir)
        assembler.assemble(recipe)
        # Assembler logs orphans/cycles as warnings usually
    except Exception as e:
        console.print(f"[red]Error:[/red] Assembly failed: {e}")
        errors += 1
        
    if errors == 0 and warnings == 0:
        console.print("[bold green]Lint Passed! ✨[/bold green]")
    else:
        console.print(f"\n[bold]Summary:[/bold] {errors} Errors, {warnings} Warnings")
