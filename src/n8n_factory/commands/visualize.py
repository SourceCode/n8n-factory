from rich.console import Console
from ..models import Recipe

console = Console()

def visualize_recipe(recipe: Recipe, format: str = "mermaid"):
    console.print(f"[bold]Generating Diagram for: {recipe.name} ({format})[/bold]")
    
    if format == "mermaid":
        lines = ["graph TD;"]
        for i, step in enumerate(recipe.steps):
            if "webhook" in step.template:
                 lines.append(f"    {step.id}([{step.id} <br/> <small>{step.template}</small>])")
            else:
                 lines.append(f"    {step.id}[{step.id} <br/> <small>{step.template}</small>]")
            
            if step.connections_from:
                for source in step.connections_from:
                    lines.append(f"    {source} --> {step.id};")
            elif i > 0:
                prev = recipe.steps[i-1].id
                lines.append(f"    {prev} --> {step.id};")
                
        diagram = "\n".join(lines)
        console.print("\n[dim]--- Copy below into mermaid.live ---\n[dim]")
        print(diagram)
        console.print("\n[dim]------------------------------------[/dim]")

    elif format == "dot":
        lines = ["digraph G {"]
        lines.append("  rankdir=TB;")
        lines.append("  node [shape=box style=filled fillcolor=lightgrey];")
        
        for i, step in enumerate(recipe.steps):
            lines.append(f'  "{step.id}" [label="{step.id}\n({step.template})"];')
            
            if step.connections_from:
                for source in step.connections_from:
                    lines.append(f'  "{source}" -> "{step.id}";')
            elif i > 0:
                prev = recipe.steps[i-1].id
                lines.append(f'  "{prev}" -> "{step.id}";')
                
        lines.append("}")
        print("\n".join(lines))

    elif format == "ascii":
        # Simple adjacency list print
        console.print("[bold]Flow Graph:[/bold]")
        for i, step in enumerate(recipe.steps):
            sources = step.connections_from
            if not sources and i > 0:
                sources = [recipe.steps[i-1].id]
            
            source_txt = ", ".join(sources) if sources else "(Start)"
            console.print(f"{source_txt} --> [bold cyan]{step.id}[/bold cyan]")