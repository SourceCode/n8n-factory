import yaml
import json
import re
from rich.console import Console
from deepdiff import DeepDiff
from ..utils import load_recipe

console = Console()

def metrics_command(recipe_path: str, json_output: bool = False):
    recipe = load_recipe(recipe_path)
    nodes = len(recipe.steps)
    # Count connections
    edges = 0
    for i, step in enumerate(recipe.steps):
        if step.connections_from:
            edges += len(step.connections_from)
        elif i > 0:
            edges += 1
            
    # Cyclomatic Complexity = E - N + 2P (P=1) -> E - N + 2
    complexity = edges - nodes + 2
    
    result = {
        "nodes": nodes,
        "edges": edges,
        "cyclomatic_complexity": complexity,
        "density": edges / nodes if nodes > 0 else 0,
        "rating": "High" if complexity > 10 else "Moderate" if complexity > 5 else "Low"
    }
    
    if json_output:
        print(json.dumps(result, indent=2))
    else:
        console.print("[bold]Metrics:[/bold]")
        console.print(result)

def fix_command(recipe_path: str, json_output: bool = False):
    # Load raw dict to preserve structure better than Pydantic dump potentially?
    # No, Pydantic dump is safer for standardizing.
    recipe = load_recipe(recipe_path)
    fixes = []
    
    for step in recipe.steps:
        # Fix 1: Missing description
        if not step.description:
            step.description = f"Step using {step.template}"
            fixes.append(f"Added description to {step.id}")
            
        # Fix 2: ID convention (simple replacement of space/dash)
        if not re.match(r'^[a-z0-9_]+$', step.id):
            old_id = step.id
            new_id = re.sub(r'[^a-z0-9_]', '_', step.id.lower())
            step.id = new_id
            fixes.append(f"Renamed ID {old_id} -> {new_id}")
            # NOTE: This breaks connections! We need to update references.
            # Complex fix. For MVP, skip ID renaming or do it carefully.
            # Let's skip ID fixing to avoid breaking graph.
            step.id = old_id 
            fixes.pop() 

    # Save back
    with open(recipe_path, 'w') as f:
        # Dump model
        data = recipe.model_dump(exclude_none=True)
        yaml.dump(data, f, sort_keys=False)
        
    if json_output:
        print(json.dumps({"fixes": fixes, "count": len(fixes)}))
    else:
        console.print(f"[green]Applied {len(fixes)} fixes.[/green]")

def suggest_command(recipe_path: str, json_output: bool = False):
    recipe = load_recipe(recipe_path)
    suggestions = []
    
    templates = [s.template for s in recipe.steps]
    
    if "webhook" in templates and "respond_to_webhook" not in templates:
        suggestions.append("Workflow has a Webhook but no 'Respond to Webhook' node.")
        
    if "if" in templates and "merge" not in templates:
        suggestions.append("Workflow splits execution (If) but might not merge it back.")
        
    if len(recipe.steps) > 20:
        suggestions.append("Workflow is large (>20 steps). Consider splitting into sub-workflows.")

    if json_output:
        print(json.dumps({"suggestions": suggestions}))
    else:
        if suggestions:
            console.print("[bold yellow]Suggestions:[/bold yellow]")
            for s in suggestions: console.print(f"- {s}")
        else:
            console.print("[green]No suggestions.[/green]")

def convert_command(input_file: str, output_file: str = None, json_output: bool = False):
    # Detect format
    if input_file.endswith(".yaml"):
        with open(input_file, 'r') as f: data = yaml.safe_load(f)
        out_ext = ".json"
    else:
        with open(input_file, 'r') as f: data = json.load(f)
        out_ext = ".yaml"
        
    if not output_file:
        base = os.path.splitext(input_file)[0]
        output_file = base + out_ext
        
    with open(output_file, 'w') as f:
        if out_ext == ".json":
            json.dump(data, f, indent=2)
        else:
            yaml.dump(data, f, sort_keys=False)
            
    if json_output:
        print(json.dumps({"converted_to": output_file}))
    else:
        console.print(f"[green]Converted to {output_file}[/green]")
