import time
from rich.console import Console
from rich.prompt import Prompt

console = Console()

def tutorial():
    console.print("[bold cyan]Welcome to n8n-factory Interactive Tutorial![/bold cyan]")
    time.sleep(1)
    
    console.print("\n[step]Step 1: Concept[/step]")
    console.print("n8n-factory lets you build workflows using simple YAML recipes instead of dragging nodes in UI.")
    Prompt.ask("Press Enter to continue")
    
    console.print("\n[step]Step 2: Templates[/step]")
    console.print("Templates are JSON files defining node defaults. You assume they exist or create new ones.")
    console.print("Try running: [green]n8n-factory list[/green] later to see them.")
    Prompt.ask("Press Enter to continue")
    
    console.print("\n[step]Step 3: Creating a Recipe[/step]")
    console.print("A recipe looks like this:")
    console.print("""[dim]\n    name: \"My Flow\"
    steps:
      - id: \"start\"
        template: \"webhook\"
        params: { path: \"hello\", method: \"GET\" }\n[/dim]""")
    
    console.print("\nYou can use [green]n8n-factory init[/green] to generate one.")
    Prompt.ask("Press Enter to continue")
    
    console.print("\n[step]Step 4: Building[/step]")
    console.print("Once you have a recipe, run:")
    console.print("[green]n8n-factory build recipes/my_flow.yaml[/green]")
    console.print("This produces a JSON file you can import into n8n.")
    
    console.print("\n[bold green]Tutorial Complete![/bold green] Happy Automating!")

if __name__ == "__main__":
    tutorial()
