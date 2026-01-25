import time
import yaml
from rich.console import Console
from ..assembler import WorkflowAssembler
from ..models import Recipe, RecipeStep

console = Console()

def benchmark_command(size: int = 1000):
    console.print(f"Benchmarking with {size} steps...")
    
    steps = []
    for i in range(size):
        steps.append(RecipeStep(
            id=f"step_{i}", 
            template="code", 
            params={"code": "return items;"}
        ))
        
    recipe = Recipe(name="Benchmark", steps=steps)
    
    start = time.time()
    assembler = WorkflowAssembler(templates_dir="templates")
    # We need a valid templates dir. If not exists, it fails.
    # We'll assume it exists or use internal mock loader if we were rigorous.
    
    assembler.assemble(recipe)
    elapsed = time.time() - start
    
    console.print(f"[bold green]Build Time:[/bold green] {elapsed:.4f}s")
    console.print(f"Steps/Sec: {size/elapsed:.2f}")
