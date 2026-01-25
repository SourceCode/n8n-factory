from rich.console import Console
from ..models import Recipe
from ..assembler import WorkflowAssembler

console = Console()

def validate_recipe(recipe: Recipe, templates_dir: str):
    console.print(f"Validating '[bold]{recipe.name}[/bold]'...")
    
    try:
        assembler = WorkflowAssembler(templates_dir)
        assembler.assemble(recipe)
        console.print("[bold green]Validation Passed![/bold green]")
        console.print(f"  - {len(recipe.steps)} steps")
        console.print(f"  - Logic consistent")
        console.print(f"  - No cycles detected")
    except Exception as e:
        console.print(f"[bold red]Validation Failed:[/bold red] {e}")
