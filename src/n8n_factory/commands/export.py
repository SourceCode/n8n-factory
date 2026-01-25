import yaml
from rich.console import Console
from ..utils import load_recipe

console = Console()

def export_command(recipe_path: str, format: str = "yaml"):
    recipe = load_recipe(recipe_path)
    
    if format == "yaml":
        data = recipe.model_dump(exclude_none=True)
        print(yaml.dump(data, sort_keys=False))
    else:
        console.print(f"[red]Format {format} not supported[/red]")
