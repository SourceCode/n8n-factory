from rich.tree import Tree
from rich.console import Console
from ..models import Recipe

console = Console()

def tree_command(recipe: Recipe):
    tree = Tree(f"[bold]{recipe.name}[/bold]")
    
    if recipe.globals:
        g_branch = tree.add("Globals")
        for k, v in recipe.globals.items():
            g_branch.add(f"{k}: {v}")
            
    if recipe.imports:
        i_branch = tree.add("Imports")
        for imp in recipe.imports:
            i_branch.add(imp)
            
    s_branch = tree.add("Steps")
    for step in recipe.steps:
        node_txt = f"[green]{step.id}[/green] ({step.template})"
        if step.disabled:
            node_txt += " [red](DISABLED)[/red]"
        step_node = s_branch.add(node_txt)
        
        # Show connections if explicit
        if step.connections_from:
            c_branch = step_node.add("From")
            for src in step.connections_from:
                c_branch.add(src)
                
    console.print(tree)
