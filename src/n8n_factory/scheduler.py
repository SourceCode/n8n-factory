import time
import json
from typing import Optional
from rich.console import Console
from .operator import SystemOperator
from .queue_manager import QueueManager
from .logger import logger

console = Console()

class Scheduler:
    def __init__(self, concurrency: int = 5, poll_interval: int = 5, broker_port: Optional[int] = None):
        self.concurrency = concurrency
        self.poll_interval = poll_interval
        self.broker_port = broker_port
        self.operator = SystemOperator()
        self.queue = QueueManager(operator=self.operator)
        self.running = False

    def start(self):
        console.print(f"[bold green]Starting Scheduler (Concurrency: {self.concurrency}, Broker Port: {self.broker_port or 'Default'})[/bold green]")
        self.running = True
        
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
        
        try:
            # We enforce a safe port for CLI execution to avoid conflicts with the main instance
            safe_env = {"N8N_PORT": "5679"}
            
            res = ""
            if mode == 'id':
                res = self.operator.execute_workflow(workflow_id=workflow, env=safe_env, broker_port=self.broker_port)
            else:
                res = self.operator.execute_workflow(file_path=workflow, env=safe_env, broker_port=self.broker_port)
            
            # Check for failure string from operator
            if res.startswith("Execution failed"):
                raise RuntimeError(res)

            logger.info(f"Execution started/result: {res}")
            
        except Exception as e:
            logger.error(f"Failed to execute job {workflow}: {e}")
            logger.warning(f"Requeueing job {workflow} due to failure.")
            self.queue.requeue(job)