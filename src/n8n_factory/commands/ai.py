import json
import sys
from rich.console import Console
from rich.markdown import Markdown
from ..ai.ollama_client import OllamaClient
from ..ai.prompt_optimizer import PromptOptimizer

console = Console()

def optimize_prompt_command(prompt: str, model: str = None, json_output: bool = False):
    """
    Optimize a prompt using the configured AI model.
    """
    optimizer = PromptOptimizer()
    if not json_output:
        console.print("[dim]Optimizing prompt...[/dim]")
        
    try:
        optimized = optimizer.optimize(prompt, model=model)
        if json_output:
            print(json.dumps({"original": prompt, "optimized": optimized}, indent=2))
        else:
            console.print("[bold green]Optimized Prompt:[/bold green]")
            console.print(optimized)
            console.print("\n[dim](Copy this prompt for better results)[/dim]")
    except Exception as e:
        if json_output:
            print(json.dumps({"error": str(e)}))
        else:
            console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)

def ask_command(prompt: str, model: str = None, system: str = None, json_output: bool = False):
    """
    Send a chat prompt to Ollama.
    """
    client = OllamaClient(model=model)
    
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    
    if not json_output:
        console.print(f"[dim]Using model: {client.model}[/dim]")
        console.print("[dim]Thinking...[/dim]")

    try:
        # We use stream=True for better UX in CLI unless json_output is requested
        if json_output:
            response = client.chat(messages, stream=False)
            print(json.dumps(response, indent=2))
        else:
            response_stream = client.chat(messages, stream=True)
            full_response = ""
            for line in response_stream.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        if "message" in chunk and "content" in chunk["message"]:
                            content = chunk["message"]["content"]
                            full_response += content
                            console.print(content, end="")
                    except json.JSONDecodeError:
                        pass
            console.print() # Newline at end
            
    except Exception as e:
        if json_output:
            print(json.dumps({"error": str(e)}))
        else:
            console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)

def list_models_command(json_output: bool = False):
    client = OllamaClient()
    try:
        models = client.list_models()
        if json_output:
            print(json.dumps(models, indent=2))
        else:
            console.print("[bold]Available Models:[/bold]")
            for m in models.get("models", []):
                console.print(f"- {m['name']} ({m['size'] / 1024 / 1024 / 1024:.2f} GB)")
    except Exception as e:
        if json_output:
            print(json.dumps({"error": str(e)}))
        else:
            console.print(f"[bold red]Error:[/bold red] {e}")
