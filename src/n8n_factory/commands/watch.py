import time
import sys
import os
import fnmatch
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from rich.console import Console
from ..assembler import WorkflowAssembler
from ..utils import load_recipe

console = Console()

class RecipeHandler(FileSystemEventHandler):
    def __init__(self, recipe_path: str, templates_dir: str):
        self.recipe_path = os.path.abspath(recipe_path)
        self.templates_dir = templates_dir
        self.assembler = WorkflowAssembler(templates_dir)
        self.ignore_patterns = []
        self._load_ignore()

    def _load_ignore(self):
        if os.path.exists(".n8nignore"):
            with open(".n8nignore", "r") as f:
                self.ignore_patterns = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    def _is_ignored(self, path):
        # Check against patterns
        # fnmatch isn't perfect for gitignore style but good enough for simple use
        rel_path = os.path.relpath(path)
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(rel_path, pattern):
                return True
        return False

    def on_modified(self, event):
        if self._is_ignored(event.src_path):
            return

        if os.path.abspath(event.src_path) == self.recipe_path:
            console.print(f"\n[bold yellow]Change detected in {self.recipe_path}. Rebuilding...[/bold yellow]")
            try:
                recipe = load_recipe(self.recipe_path)
                self.assembler.assemble(recipe)
                console.print(f"[bold green]Rebuild Successful at {time.strftime('%X')}[/bold green]")
            except Exception as e:
                console.print(f"[bold red]Build Failed:[/bold red] {e}")

def watch_recipe(recipe_path: str, templates_dir: str):
    if not os.path.exists(recipe_path):
        console.print(f"[bold red]Error:[/bold red] File {recipe_path} not found.")
        return

    event_handler = RecipeHandler(recipe_path, templates_dir)
    observer = Observer()
    watch_dir = os.path.dirname(os.path.abspath(recipe_path))
    observer.schedule(event_handler, watch_dir, recursive=False)
    
    console.print(f"[bold blue]Watching {recipe_path} for changes... (Ctrl+C to stop)[/bold blue]")
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
