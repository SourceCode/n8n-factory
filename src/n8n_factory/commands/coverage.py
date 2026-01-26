import json
import os
from rich.console import Console
from ..models import Recipe

console = Console()

def coverage_command(recipe: Recipe, simulation_json: str, json_output: bool = False):
    if not os.path.exists(simulation_json):
        err = f"Simulation history not found: {simulation_json}"
        if json_output: print(json.dumps({"error": err})); return
        else: console.print(f"[red]{err}[/red]"); return

    with open(simulation_json, 'r', encoding='utf-8') as f:
        history = json.load(f)
        
    executed_steps = set()
    # History structure depends on simulator.py output. 
    # Usually list of dicts with 'step_id' or similar.
    # Checking simulator.py logic (assumed): list of execution events.
    
    for event in history:
        # Simulator output format check: usually a list of step outputs.
        # Assuming event is dict and has step info. 
        # If it's just the output data, we might not have step_id directly unless simulator provides it.
        # I'll assume simulator tracks 'step' or 'node'.
        sid = event.get("step_id") or event.get("node")
        if sid:
            executed_steps.add(sid)
            
    all_steps = set(s.id for s in recipe.steps)
    missed = all_steps - executed_steps
    
    coverage_pct = (len(executed_steps) / len(all_steps)) * 100 if all_steps else 0
    
    result = {
        "coverage_percent": round(coverage_pct, 2),
        "total_steps": len(all_steps),
        "executed_count": len(executed_steps),
        "executed_steps": list(executed_steps),
        "missed_steps": list(missed)
    }
    
    if json_output:
        print(json.dumps(result, indent=2))
    else:
        color = "green" if coverage_pct == 100 else "yellow" if coverage_pct > 50 else "red"
        console.print(f"Coverage: [{color}]{coverage_pct:.1f}%[/{color}]")
        if missed:
            console.print(f"[dim]Missed:[/dim] {', '.join(missed)}")
