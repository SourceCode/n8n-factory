from rich.console import Console
from ..utils import load_recipe

console = Console()

def info_command(recipe_path: str):
    # Load raw to show imports properly?
    # load_recipe merges imports.
    # To show structure we might want to inspect raw yaml first?
    # But let's show the resolved view.
    
    recipe = load_recipe(recipe_path)
    
    console.print(f"[bold]Recipe Info:[/bold] {recipe.name}")
    if recipe.description:
        console.print(f"[dim]{recipe.description}[/dim]")
        
    console.print(f"\nSteps: [cyan]{len(recipe.steps)}[/cyan]")
    console.print(f"Imports: [cyan]{len(recipe.imports)}[/cyan]")
    console.print(f"Globals: {list(recipe.globals.keys())}")
    console.print(f"Tags: {recipe.tags}")

