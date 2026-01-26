import json
from rich.console import Console
from ..utils import load_recipe

console = Console()

def cost_command(recipe_path: str, json_output: bool = False):
    recipe = load_recipe(recipe_path)
    
    node_count = len(recipe.steps)
    
    # Analyze complexity
    expensive_nodes = []
    loops = 0
    for step in recipe.steps:
        if "openai" in step.template or "ai" in step.template:
            expensive_nodes.append(step.id)
        if "split" in step.template or "merge" in step.template:
            # potential loop or branching
            pass
            
    # Estimate execution units
    # Base: 1 unit per node
    # AI: 10 units?
    est_units = node_count + (len(expensive_nodes) * 9)
    
    result = {
        "nodes": node_count,
        "expensive_nodes": expensive_nodes,
        "estimated_execution_units": est_units,
        "rating": "Low" if est_units < 20 else "Medium" if est_units < 100 else "High"
    }
    
    if json_output:
        print(json.dumps(result, indent=2))
    else:
        console.print("[bold]Cost Estimation[/bold]")
        console.print(result)
