from rich.console import Console
from ..models import Recipe
import json
import re

console = Console()

def visualize_recipe(recipe: Recipe, format: str = "mermaid"):
    # If JSON format, just output JSON and return, don't print rich headers
    if format == "json":
        nodes = []
        edges = []
        node_ids = set(s.id for s in recipe.steps)
        
        # 1. Flow Edges
        for i, step in enumerate(recipe.steps):
            nodes.append({"id": step.id, "template": step.template})
            sources = []
            if step.connections_from:
                for s in step.connections_from:
                    s_id = s if isinstance(s, str) else s.node
                    sources.append(s_id)
            elif i > 0:
                sources.append(recipe.steps[i-1].id)
            
            for s in sources:
                edges.append({"source": s, "target": step.id, "type": "flow"})
        
        # 2. Expression Edges
        pattern = re.compile(r'\$node\[["\'](.*?)["\']\]')
        for step in recipe.steps:
            for v in step.params.values():
                matches = pattern.findall(str(v))
                for m in matches:
                    if m in node_ids:
                        edges.append({"source": m, "target": step.id, "type": "expression"})
        
        graph = {"nodes": nodes, "edges": edges}
        print(json.dumps(graph, indent=2))
        return

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
                    # Handle Connection objects
                    s_id = source if isinstance(source, str) else source.node
                    lines.append(f"    {s_id} --> {step.id};")
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
                    s_id = source if isinstance(source, str) else source.node
                    lines.append(f'  "{s_id}" -> "{step.id}";')
            elif i > 0:
                prev = recipe.steps[i-1].id
                lines.append(f'  "{prev}" -> "{step.id}";')
                
        lines.append("}")
        print("\n".join(lines))

    elif format == "ascii":
        # Simple adjacency list print
        console.print("[bold]Flow Graph:[/bold]")
        for i, step in enumerate(recipe.steps):
            sources = []
            if step.connections_from:
                for s in step.connections_from:
                    sources.append(s if isinstance(s, str) else s.node)
            elif i > 0:
                sources = [recipe.steps[i-1].id]
            
            source_txt = ", ".join(sources) if sources else "(Start)"
            console.print(f"{source_txt} --> [bold cyan]{step.id}[/bold cyan]")