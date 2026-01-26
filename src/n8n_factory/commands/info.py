from rich.console import Console
from ..utils import load_recipe
import json

console = Console()

def info_command(recipe_path: str, dependencies: bool = False, json_output: bool = False):
    recipe = load_recipe(recipe_path)
    
    templates_used = sorted(list(set([s.template for s in recipe.steps])))
    
    info = {
        "name": recipe.name,
        "description": recipe.description,
        "step_count": len(recipe.steps),
        "tags": recipe.tags,
        "globals": list(recipe.globals.keys()),
        "imports": [str(i.path if hasattr(i, 'path') else i) for i in recipe.imports]
    }
    
    if dependencies:
        info["dependencies"] = {
            "templates": templates_used
        }

    if json_output:
        print(json.dumps(info, indent=2))
        return

    console.print(f"[bold]Recipe Info:[/bold] {recipe.name}")
    if recipe.description:
        console.print(f"[dim]{recipe.description}[/dim]")
        
    console.print(f"\nSteps: [cyan]{len(recipe.steps)}[/cyan]")
    console.print(f"Imports: [cyan]{len(recipe.imports)}[/cyan]")
    console.print(f"Globals: {list(recipe.globals.keys())}")
    console.print(f"Tags: {recipe.tags}")
    
    if dependencies:
        console.print("\n[bold]Templates Used:[/bold]")
        for t in templates_used:
            console.print(f"- {t}")