import json
import os
import yaml
from deepdiff import DeepDiff
from rich.console import Console
from rich.syntax import Syntax
from ..utils import load_recipe
from ..assembler import WorkflowAssembler

console = Console(record=True) # Enable recording for HTML export

def diff_recipe(recipe_path: str, target_path: str, templates_dir: str, html_output: str = None, summary: bool = False, json_output: bool = False):
    # Source is always the recipe built fresh
    recipe = load_recipe(recipe_path)
    assembler = WorkflowAssembler(templates_dir)
    current_build = assembler.assemble(recipe)
    
    # Target can be another recipe or a built json file
    if target_path.endswith(".yaml"):
        target_recipe = load_recipe(target_path)
        target_build = assembler.assemble(target_recipe)
    elif target_path.endswith(".json"):
        with open(target_path, 'r', encoding='utf-8') as f:
            target_build = json.load(f)
    else:
        err = "Target must be .yaml (recipe) or .json (workflow)"
        if json_output:
            print(json.dumps({"error": err}))
        else:
            console.print(f"[red]{err}[/red]")
        return

    exclude_paths = ["root['meta']['generatedAt']", "root['meta']['instanceId']"]
    
    diff = DeepDiff(target_build, current_build, ignore_order=True, exclude_paths=exclude_paths)
    
    if summary:
        added = list(diff.get('dictionary_item_added', []))
        removed = list(diff.get('dictionary_item_removed', []))
        changed = list(diff.get('values_changed', []))
        
        summ = {
            "status": "diff_found" if diff else "identical",
            "counts": {
                "added": len(added),
                "removed": len(removed),
                "changed": len(changed)
            },
            "details": {
                "added": added,
                "removed": removed,
                "changed_keys": list(changed.keys()) if isinstance(changed, dict) else changed
            }
        }
        if json_output:
            print(json.dumps(summ, indent=2))
        else:
            console.print("[bold]Diff Summary:[/bold]")
            console.print(summ)
        return

    if json_output:
        print(diff.to_json(indent=2))
        return

    if not diff:
        console.print("[bold green]No differences found.[/bold green]")
    else:
        console.print("[bold yellow]Differences Detected:[/bold yellow]")
        # DeepDiff output can be messy to read directly, usually we rely on to_json or manual parsing
        # For CLI viewing, let's just print json repr for now
        console.print(diff.to_json(indent=2))
        
    if html_output:
        console.save_html(html_output)
        print(f"HTML Diff saved to {html_output}")
