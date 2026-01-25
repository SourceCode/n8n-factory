import http.server
import socketserver
import webbrowser
from rich.console import Console
from ..utils import load_recipe
from ..assembler import WorkflowAssembler # For graph structure logic? Or duplicate?
# Actually visualize command uses internal logic.
# I should reuse visualize logic or export graph.
# Let's import visualize logic if possible, or duplicate for now as serve is standalone.
from ..graph import DependencyGraph

console = Console()

def serve_command(recipe_path: str, port: int = 8000):
    recipe = load_recipe(recipe_path)
    graph = DependencyGraph(recipe.steps)
    mermaid_def = graph.to_mermaid()
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>n8n Factory - {recipe.name}</title>
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ startOnLoad: true }});
        </script>
    </head>
    <body>
        <h1>{recipe.name}</h1>
        <div class="mermaid">
            {mermaid_def}
        </div>
    </body>
    </html>
    """
    
    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(html_content.encode("utf-8"))
            
    with socketserver.TCPServer(("", port), Handler) as httpd:
        console.print(f"Serving at [bold]http://localhost:{port}[/bold]")
        webbrowser.open(f"http://localhost:{port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
