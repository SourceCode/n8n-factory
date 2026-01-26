import json
from rich.console import Console
from ..utils import load_recipe

console = Console()

def mock_generate_command(recipe_path: str, output_file: str = None, json_output: bool = False):
    recipe = load_recipe(recipe_path)
    if not recipe.steps:
        if json_output: print(json.dumps({"error": "Recipe has no steps"}))
        else: console.print("[red]Recipe has no steps[/red]")
        return

    start_step = recipe.steps[0]
    
    mock_data = {}
    if "webhook" in start_step.template.lower():
        mock_data = {
            "headers": {"content-type": "application/json"},
            "params": {},
            "query": {},
            "body": {"test": "data"}
        }
    elif "cron" in start_step.template.lower() or "schedule" in start_step.template.lower():
        mock_data = {"timestamp": 1234567890}
    else:
        mock_data = {"json": {"input": "value"}}
        
    if not output_file:
        output_file = "mock.json"
        
    with open(output_file, 'w') as f:
        json.dump([mock_data], f, indent=2)
        
    if json_output:
        print(json.dumps({"status": "generated", "file": output_file}))
    else:
        console.print(f"[green]Mock data generated:[/green] {output_file}")
