import os
import shutil
import datetime
import json
from rich.console import Console

console = Console()

def backup_command(target_dir: str = "recipes", json_output: bool = False):
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"backups/{target_dir}_{ts}"
    
    if not os.path.exists("backups"):
        os.makedirs("backups")
        
    try:
        shutil.copytree(target_dir, backup_path)
        if json_output:
            print(json.dumps({"status": "success", "backup_path": backup_path}))
        else:
            console.print(f"[bold green]Backup created:[/bold green] {backup_path}")
    except Exception as e:
        if json_output:
            print(json.dumps({"error": str(e)}))
        else:
            console.print(f"[red]Backup failed: {e}[/red]")

def test_scaffold_command(recipe_path: str, output_file: str = None, json_output: bool = False):
    base_name = os.path.splitext(os.path.basename(recipe_path))[0]
    if not output_file:
        output_file = f"tests/test_{base_name}.py"
        
    if not os.path.exists("tests"):
        os.makedirs("tests")
        
    content = f"""import pytest
from src.n8n_factory.utils import load_recipe
from src.n8n_factory.simulator import WorkflowSimulator

def test_{base_name}_simulation():
    recipe = load_recipe("{recipe_path}")
    simulator = WorkflowSimulator()
    history = simulator.simulate(recipe, max_steps=50)
    
    # Basic Assertion: Workflow ran
    assert len(history) > 0
    
    # TODO: Add specific assertions
    # last_node = history[-1]
    # assert last_node['step_id'] == 'expected_end'
"""
    with open(output_file, 'w') as f:
        f.write(content)
        
    if json_output:
        print(json.dumps({"status": "created", "test_file": output_file}))
    else:
        console.print(f"[bold green]Test scaffold created:[/bold green] {output_file}")

def env_command(action: str, key: str = None, value: str = None, json_output: bool = False):
    env_file = ".env"
    current_env = {}
    
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    current_env[k] = v
                    
    if action == "list":
        if json_output:
            print(json.dumps(current_env, indent=2))
        else:
            for k, v in current_env.items():
                console.print(f"{k}={v}")
                
    elif action == "get":
        val = current_env.get(key)
        if json_output:
            print(json.dumps({key: val}))
        else:
            console.print(val if val else "[dim]Not set[/dim]")
            
    elif action == "set":
        current_env[key] = value
        with open(env_file, 'w') as f:
            for k, v in current_env.items():
                f.write(f"{k}={v}\n")
        if json_output:
            print(json.dumps({"status": "updated", key: value}))
        else:
            console.print(f"[green]Set {key}[/green]")
