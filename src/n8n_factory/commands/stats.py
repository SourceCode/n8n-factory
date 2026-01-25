from rich.console import Console
from tabulate import tabulate
from ..models import Recipe

console = Console()

def stats_command(recipe: Recipe):
    console.print(f"[bold]Statistics for '{recipe.name}'[/bold]")
    
    node_counts = {}
    for step in recipe.steps:
        node_counts[step.template] = node_counts.get(step.template, 0) + 1
        
    total_steps = len(recipe.steps)
    
    # Calculate Complexity (simple heuristic: connections + nodes)
    # Actually we don't have connection count easily available in Recipe object alone without assembly
    # But we can count explicit connections
    explicit_conns = sum(len(step.connections_from) for step in recipe.steps if step.connections_from)
    complexity = total_steps + explicit_conns
    
    data = [[k, v] for k, v in node_counts.items()]
    data.sort(key=lambda x: x[1], reverse=True)
    
    console.print(f"\nTotal Steps: [cyan]{total_steps}[/cyan]")
    console.print(f"Complexity Score: [magenta]{complexity}[/magenta]")
    console.print(f"Tags: {', '.join(recipe.tags)}")
    
    console.print("\n[bold]Node Type Distribution:[/bold]")
    console.print(tabulate(data, headers=["Template", "Count"], tablefmt="simple"))

