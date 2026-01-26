import os
import json
import glob
import yaml
from rich.console import Console
from rich.tree import Tree
from ..utils import load_recipe

console = Console()

def context_command(json_output: bool = False):
    """
    Dumps the current project context for an AI agent.
    """
    cwd = os.getcwd()
    
    # File Structure
    ignore = {'.git', '__pycache__', '.pytest_cache', 'venv', 'env'}
    file_tree = {}
    for root, dirs, files in os.walk(cwd):
        dirs[:] = [d for d in dirs if d not in ignore]
        rel_root = os.path.relpath(root, cwd)
        if rel_root == ".": rel_root = ""
        
        dir_files = [f for f in files if not f.endswith('.pyc')]
        if dir_files:
            file_tree[rel_root] = dir_files

    # Counts
    recipe_count = len(glob.glob("recipes/*.yaml"))
    template_count = len(glob.glob("templates/*.json"))
    
    # Env Vars present (keys only)
    env_keys = list(os.environ.keys())
    
    context = {
        "cwd": cwd,
        "structure": file_tree,
        "counts": {
            "recipes": recipe_count,
            "templates": template_count
        },
        "environment_keys": env_keys,
        "config_present": os.path.exists(".n8n-factory.yaml")
    }
    
    if json_output:
        print(json.dumps(context, indent=2))
    else:
        console.print("[bold]Project Context[/bold]")
        tree = Tree(f"📁 {os.path.basename(cwd)}")
        for d, files in file_tree.items():
            if d == "":
                for f in files: tree.add(f"📄 {f}")
            else:
                branch = tree.add(f"📂 {d}")
                for f in files: branch.add(f"📄 {f}")
        console.print(tree)
        console.print(f"\nRecipes: {recipe_count}, Templates: {template_count}")

def catalog_command(templates_dir: str = "templates", json_output: bool = False):
    """
    Generates a detailed registry of all templates.
    """
    catalog = []
    files = glob.glob(os.path.join(templates_dir, "*.json"))
    
    for f in sorted(files):
        try:
            with open(f, 'r', encoding='utf-8') as tf:
                data = json.load(tf)
                meta = data.get("_meta", {})
                item = {
                    "name": os.path.basename(f).replace(".json", ""),
                    "type": data.get("type"),
                    "required_params": meta.get("required_params", []),
                    "description": meta.get("description", "")
                }
                catalog.append(item)
        except:
            pass
            
    if json_output:
        print(json.dumps(catalog, indent=2))
    else:
        console.print(f"[bold]Template Catalog ({len(catalog)} items)[/bold]")
        for item in catalog:
            console.print(f"- [cyan]{item['name']}[/cyan] ({item['type']})")
            if item['required_params']:
                console.print(f"  Req: {', '.join(item['required_params'])}", style="dim")

def usage_command(template_name: str, recipes_dir: str = "recipes", json_output: bool = False):
    """
    Finds recipes that use a specific template.
    """
    matches = []
    recipe_files = glob.glob(os.path.join(recipes_dir, "**/*.yaml"), recursive=True)
    
    for rf in recipe_files:
        try:
            with open(rf, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
                if not content: continue
                steps = content.get("steps", [])
                for step in steps:
                    if step.get("template") == template_name:
                        matches.append(rf)
                        break
        except:
            pass
            
    if json_output:
        print(json.dumps({"template": template_name, "used_in": matches}, indent=2))
    else:
        console.print(f"[bold]Usages of '{template_name}':[/bold]")
        for m in matches:
            console.print(f"- {m}")
