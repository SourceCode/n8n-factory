import json
import sys
from rich.console import Console
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
    client = OllamaClient(model=model or "qwen3:8b")
    
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    
    if not json_output:
        console.print(f"[dim]Using model: {client.model}[/dim]")
        console.print("[dim]Thinking...[/dim]")

    try:
        if json_output:
            response = client.chat(messages, stream=False)
            print(json.dumps(response, indent=2))
        else:
            # Basic non-streaming fallback for now until client supports streaming
            response = client.chat(messages, stream=False)
            console.print(response.get("content", ""))
            
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
            for m in models:
                size_gb = m.get('size', 0) / 1024 / 1024 / 1024
                console.print(f"- {m['name']} ({size_gb:.2f} GB)")
    except Exception as e:
        if json_output:
            print(json.dumps({"error": str(e)}))
        else:
            console.print(f"[bold red]Error:[/bold red] {e}")