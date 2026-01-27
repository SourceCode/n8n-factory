import json
import sys
from typing import Optional
from rich.console import Console
from rich.table import Table
from ..queue_manager import QueueManager
from ..scheduler import Scheduler
from ..control_plane import AdaptiveBatchSizer, PhaseGate
from ..operator import SystemOperator

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

def schedule_add_command(workflow: str, mode: str = "id", data: str = "{}", meta: str = "{}", delay: int = 0):
    """
    Adds a job to the queue.
    """
    queue = QueueManager()
    try:
        inputs = json.loads(data)
    except json.JSONDecodeError:
        console.print("[red]Invalid JSON data[/red]")
        sys.exit(1)

    try:
        meta_dict = json.loads(meta)
    except json.JSONDecodeError:
        console.print("[red]Invalid JSON meta[/red]")
        sys.exit(1)

    queue.enqueue(workflow, inputs=inputs, mode=mode, meta=meta_dict, delay=delay)
    
    msg = f"[green]Job added to queue.[/green] Workflow: {workflow}"
    if delay > 0:
        msg += f" (Delayed: {delay}ms)"
    console.print(msg)

def schedule_list_command(limit: int = 20, json_output: bool = False):
    """
    Lists jobs in the queue.
    """
    queue = QueueManager()
    total_size = queue.size()
    delayed_size = queue.delayed_size()
    jobs = queue.list_jobs(limit=limit)
    
    if json_output:
        print(json.dumps({"total": total_size, "delayed": delayed_size, "jobs": jobs}, indent=2))
        return

    if not jobs and total_size == 0 and delayed_size == 0:
        console.print("[yellow]Queue is empty.[/yellow]")
        return

    table = Table(title=f"Job Queue (Total: {total_size}, Delayed: {delayed_size}, Showing first {limit})")
    table.add_column("Workflow", style="cyan")
    table.add_column("Mode", style="magenta")
    table.add_column("Inputs", style="dim")
    table.add_column("Retries", style="red")

    for job in jobs:
        table.add_row(
            job.get("workflow"),
            job.get("mode"),
            str(job.get("inputs"))[:50] + "...",
            str(job.get("retries", 0))
        )
    console.print(table)

def schedule_clear_command():
    queue = QueueManager()
    queue.clear()
    console.print("[green]Queue cleared.[/green]")

def schedule_reset_cursors_command(run_id: str):
    queue = QueueManager()
    queue.reset_cursors(run_id)
    console.print(f"[green]Cursors reset for run_id: {run_id}[/green]")

def schedule_control_batch(action: str, key: Optional[str] = None, value: Optional[str] = None):
    operator = SystemOperator()
    sizer = AdaptiveBatchSizer(operator)
    
    if action == "get":
        config = sizer.get_config()
        current = sizer.get_batch_size()
        console.print(f"Current Batch Size: [bold green]{current}[/bold green]")
        console.print("Configuration:")
        console.print(json.dumps(config, indent=2))
    elif action == "set":
        # Hacky config update via raw redis for now or specialized method
        if not key or not value:
            console.print("[red]Must provide key and value[/red]")
            return
        
        # We need to update the JSON blob
        config = sizer.get_config()
        try:
            # try parsing value as int/float
            if "." in value: val_parsed = float(value)
            else: val_parsed = int(value)
        except:
            val_parsed = value
            
        config[key] = val_parsed
        operator.inspect_redis(["SET", sizer.KEY_CONFIG, json.dumps(config)])
        console.print(f"[green]Updated {key} to {val_parsed}[/green]")

def schedule_control_gate(action: str, phase: str, dependency: Optional[str] = None, condition: str = "complete"):
    operator = SystemOperator()
    gate = PhaseGate(operator)
    
    if action == "set":
        if not dependency:
            console.print("[red]Must provide dependency phase[/red]")
            return
        gate.set_rule(phase, dependency, condition)
        console.print(f"[green]Gate set: {phase} depends on {dependency} ({condition})[/green]")
    elif action == "get":
        rule = gate.get_rule(phase)
        if rule:
            console.print(f"[bold]{phase}[/bold]: {json.dumps(rule)}")
        else:
            console.print(f"No gate rule for {phase}")
