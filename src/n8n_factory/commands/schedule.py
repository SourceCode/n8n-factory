import json
import sys
from typing import Optional
from rich.console import Console
from rich.table import Table
from ..queue_manager import QueueManager
from ..scheduler import Scheduler

console = Console()

def schedule_worker_command(concurrency: int = 5, poll: int = 5):
    """
    Starts the worker process.
    """
    scheduler = Scheduler(concurrency=concurrency, poll_interval=poll)
    scheduler.start()

def schedule_run_command(concurrency: int = 5, poll: int = 5, broker_port: Optional[int] = None):
    """
    Starts the queue consumer (worker) with optional broker port override.
    """
    scheduler = Scheduler(concurrency=concurrency, poll_interval=poll, broker_port=broker_port)
    scheduler.start()

def schedule_add_command(workflow: str, mode: str = "id", data: str = "{}"):
    """
    Adds a job to the queue.
    """
    queue = QueueManager()
    try:
        inputs = json.loads(data)
    except json.JSONDecodeError:
        console.print("[red]Invalid JSON data[/red]")
        sys.exit(1)

    queue.enqueue(workflow, inputs=inputs, mode=mode)
    console.print(f"[green]Job added to queue.[/green] Workflow: {workflow}")

def schedule_list_command(limit: int = 20, json_output: bool = False):
    """
    Lists jobs in the queue.
    """
    queue = QueueManager()
    total_size = queue.size()
    jobs = queue.list_jobs(limit=limit)
    
    if json_output:
        print(json.dumps({"total": total_size, "jobs": jobs}, indent=2))
        return

    if not jobs and total_size == 0:
        console.print("[yellow]Queue is empty.[/yellow]")
        return

    table = Table(title=f"Job Queue (Total: {total_size}, Showing first {limit})")
    table.add_column("Workflow", style="cyan")
    table.add_column("Mode", style="magenta")
    table.add_column("Inputs", style="dim")

    for job in jobs:
        table.add_row(
            job.get("workflow"),
            job.get("mode"),
            str(job.get("inputs"))[:50] + "..."
        )
    console.print(table)

def schedule_clear_command():
    queue = QueueManager()
    queue.clear()
    console.print("[green]Queue cleared.[/green]")
