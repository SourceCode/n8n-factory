import os
from rich.prompt import Prompt
from rich.console import Console

console = Console()

def login_command():
    console.print("[bold blue]n8n Factory - Setup[/bold blue]")
    
    url = Prompt.ask("n8n Instance URL (e.g. https://n8n.example.com)")
    api_key = Prompt.ask("n8n API Key", password=True)
    
    env_content = ""
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            env_content = f.read()
            
    # Simple replace or append
    new_lines = []
    has_url = False
    has_key = False
    
    for line in env_content.splitlines():
        if line.startswith("N8N_URL="):
            new_lines.append(f"N8N_URL={url}")
            has_url = True
        elif line.startswith("N8N_API_KEY="):
            new_lines.append(f"N8N_API_KEY={api_key}")
            has_key = True
        else:
            new_lines.append(line)
            
    if not has_url:
        new_lines.append(f"N8N_URL={url}")
    if not has_key:
        new_lines.append(f"N8N_API_KEY={api_key}")
        
    with open(".env", "w") as f:
        f.write("\n".join(new_lines) + "\n")
        
    console.print("[bold green]Credentials saved to .env[/bold green]")
