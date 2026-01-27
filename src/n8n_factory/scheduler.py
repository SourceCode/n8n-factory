import time
import json
from typing import Optional
from rich.console import Console
from .operator import SystemOperator
from .queue_manager import QueueManager
from .logger import logger

console = Console()

class Scheduler:
    def __init__(self, concurrency: int = 5, poll_interval: int = 5):
        self.concurrency = concurrency
        self.poll_interval = poll_interval
        self.operator = SystemOperator()
        self.queue = QueueManager(operator=self.operator)
        self.running = False

    def start(self):
        self.running = True
        console.print(f"[bold green]Starting Scheduler (Concurrency: {self.concurrency})[/bold green]")
        
        while self.running:
            try:
                self._tick()
                time.sleep(self.poll_interval)
            except KeyboardInterrupt:
                console.print("\n[yellow]Stopping scheduler...[/yellow]")
                self.running = False
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(self.poll_interval)

    def _tick(self):
        # 1. Check active executions
        active_execs = self.operator.get_active_executions()
        active_count = len(active_execs)
        
        # 2. Check slots
        slots_available = self.concurrency - active_count
        
        if slots_available > 0:
            # 3. Check queue
            queue_size = self.queue.size()
            if queue_size > 0:
                logger.info(f"Slots available: {slots_available}. Queue size: {queue_size}")
                
                # Dequeue and run up to slots_available
                for _ in range(slots_available):
                    job = self.queue.dequeue()
                    if not job:
                        break
                    
                    self._execute_job(job)
            else:
                # logger.debug("Queue empty.")
                pass
        else:
            logger.debug(f"Max concurrency reached ({active_count}/{self.concurrency}).")

    def _execute_job(self, job: dict):
        workflow = job.get("workflow")
        mode = job.get("mode")
        # Ensure default is empty dict, using single braces
        inputs = job.get("inputs", dict())
        
        console.print(f"[blue]Starting job:[/blue] {workflow}")
        
        # Note: 'execute_workflow' in operator currently just runs it. 
        # Passing inputs/data via CLI is tricky with n8n execute.
        # CLI supports `--file` for workflow input, but for DATA input?
        # n8n execute does not easily support passing execution data/variables via CLI args.
        # It typically runs the workflow. 
        # If the workflow needs input, it usually comes from a Trigger or we must use webhook trigger.
        
        # If mode is 'id', we use `n8n execute --id <id>`
        # If the user wants to pass data, we might need `trigger_webhook` if it's a webhook workflow?
        # But `queue` implies we are driving it.
        
        # Limit: The current SystemOperator.execute_workflow only does --id or --file.
        # It doesn't support injecting custom data.
        # We will proceed with basic execution. 
        
        try:
            if mode == 'id':
                res = self.operator.execute_workflow(workflow_id=workflow)
            else:
                res = self.operator.execute_workflow(file_path=workflow)
                
            logger.info(f"Execution started/result: {res}")
            
        except Exception as e:
            logger.error(f"Failed to execute job {workflow}: {e}")