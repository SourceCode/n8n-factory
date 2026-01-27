import time
import json
import sys
from rich.console import Console
from rich.table import Table
from rich.live import Live
from ..operator import SystemOperator

console = Console()
operator = SystemOperator()

def ops_monitor_command(watch_id: str = None, json_output: bool = False):
    """
    Monitors n8n executions.
    If watch_id is provided, watches a specific execution.
    Otherwise, lists active executions.
    """
    if watch_id:
        _watch_execution(watch_id, json_output)
    else:
        _list_active_executions(json_output)

def _list_active_executions(json_output: bool):
    try:
        executions = operator.get_active_executions()
        
        if json_output:
            print(json.dumps(executions, indent=2))
            return

        if not executions:
            console.print("[yellow]No active executions found.[/yellow]")
            return

        table = Table(title="Active n8n Executions")
        table.add_column("ID", style="cyan")
        table.add_column("Workflow", style="green")
        table.add_column("Mode", style="magenta")
        table.add_column("Started At", style="blue")
        table.add_column("Status", style="bold yellow")

        for exec in executions:
            table.add_row(
                str(exec.get("id")),
                exec.get("name") or "Unknown",
                exec.get("mode"),
                exec.get("startedAt"),
                exec.get("status")
            )
        
        console.print(table)

    except Exception as e:
        if json_output:
            print(json.dumps({"error": str(e)}))
        else:
            console.print(f"[bold red]Error listing executions:[/bold red] {e}")

def _watch_execution(execution_id: str, json_output: bool):
    """
    Polls a specific execution and shows progress.
    """
    if json_output:
        # Just get status once
        details = operator.get_execution_details(execution_id)
        print(json.dumps(details, indent=2))
        return

    console.print(f"[bold]Watching execution {execution_id}...[/bold]")
    console.print("Press Ctrl+C to stop.")

    try:
        with Live(console=console, refresh_per_second=1) as live:
            while True:
                details = operator.get_execution_details(execution_id)
                if not details:
                    live.update(f"[red]Execution {execution_id} not found.[/red]")
                    break

                status = details.get("status")
                workflow_name = details.get("name") or "Unknown"
                
                # Parse progress
                last_node = "Unknown"
                node_count = 0
                
                data_str = details.get("data")
                if data_str:
                    try:
                        # In n8n DB, 'data' is text, so we parse it if it's a string
                        # The operator.run_db_query already attempts json.loads on the ROW, 
                        # but 'data' column content might still be a string if postgres returned it as text inside the json row.
                        # Wait, run_db_query: "SELECT row_to_json(t) ..."
                        # Postgres row_to_json should handle JSONB columns correctly as nested objects.
                        # If 'data' is text type in DB, it will be string. If JSONB, it will be object.
                        # Assuming it's an object or parseable string.
                        
                        data_obj = data_str
                        if isinstance(data_str, str):
                            data_obj = json.loads(data_str)
                            
                        result_data = data_obj.get("resultData", {})
                        last_node = result_data.get("lastNodeExecuted", "Starting...")
                        run_data = result_data.get("runData", {})
                        node_count = len(run_data.keys())
                        
                    except Exception:
                        pass

                # Build display
                content = f"""
[bold cyan]Execution ID:[/bold cyan] {execution_id}
[bold green]Workflow:[/bold green]     {workflow_name}
[bold magenta]Status:[/bold magenta]       {status}
[bold blue]Last Node:[/bold blue]    {last_node}
[bold white]Nodes Run:[/bold white]    {node_count}
                """
                
                if status == "running":
                    content += "\n[yellow]Running...[/yellow]"
                elif status == "success":
                    content += "\n[bold green]Completed Successfully![/bold green]"
                elif status == "error":
                    content += "\n[bold red]Failed![/bold red]"
                
                live.update(content)
                
                if status in ["success", "error", "canceled"]:
                    break
                    
                time.sleep(1)

    except KeyboardInterrupt:
        console.print("\n[dim]Stopped watching.[/dim]")
    except Exception as e:
        console.print(f"\n[bold red]Error watching execution:[/bold red] {e}")
