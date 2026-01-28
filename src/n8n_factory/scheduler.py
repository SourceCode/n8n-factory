import time
import json
import os
from typing import Optional
from rich.console import Console
from .operator import SystemOperator
from .queue_manager import QueueManager
from .control_plane import AdaptiveBatchSizer, PhaseGate, AutoRefiller
from .logger import logger

console = Console()

class Scheduler:
    def __init__(self, concurrency: int = 5, poll_interval: int = 5, broker_port: Optional[int] = None, refill_command: Optional[str] = None, refill_threshold: int = 5):
        self.concurrency = concurrency
        self.poll_interval = poll_interval
        self.broker_port = broker_port
        self.refill_command = refill_command
        self.refill_threshold = refill_threshold
        
        self.operator = SystemOperator()
        self.queue = QueueManager(operator=self.operator)
        self.sizer = AdaptiveBatchSizer(self.operator)
        self.gate = PhaseGate(self.operator)
        self.refiller = AutoRefiller(self.operator)
        
        self.running = False
        self.jobs_processed_session = 0
        
        # Ensure log directory exists
        self.job_log_file = os.getenv("N8N_FACTORY_LOG_PATH", "logs/jobs.jsonl")
        log_dir = os.path.dirname(self.job_log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

    def start(self):
        console.print(f"[bold green]Starting Scheduler (Concurrency: {self.concurrency}, Broker Port: {self.broker_port or 'Default'})[/bold green]")
        if self.refill_command:
            console.print(f"[cyan]Auto-refill enabled (Threshold: {self.refill_threshold}):[/cyan] {self.refill_command}")
            
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
        
        # 3. Check queue sizes (needed for refill check regardless of slots)
        queue_size = self.queue.size()
        delayed_size = self.queue.delayed_size()
        total_queued = queue_size + delayed_size

        # --- Auto Refill Check ---
        if self.refill_command:
            self.refiller.check_and_refill(total_queued, self.refill_threshold, self.refill_command)
        
        if slots_available > 0:
            if total_queued > 0:
                logger.info(f"Slots available: {slots_available}. Queue size: {queue_size} (Delayed: {delayed_size})")
                
                # Dequeue and run up to slots_available
                # Note: dequeue checks delayed queue automatically
                for _ in range(slots_available):
                    job = self.queue.dequeue()
                    if not job:
                        break
                    
                    self._execute_job(job)
            else:
                # Queue is empty. Check cursors for warning.
                # Heuristic: If we have active run_ids with remaining items, warn.
                # This is tricky without knowing *which* run_ids are active. 
                # We can check if any gate is blocked? No.
                # Ideally, we'd need a registry of active runs. 
                # For now, we skip generic warning to avoid noise unless we have specific context.
                pass
        else:
            logger.debug(f"Max concurrency reached ({active_count}/{self.concurrency}).")

    def _execute_job(self, job: dict):
        workflow = job.get("workflow")
        mode = job.get("mode")
        meta = job.get("meta", {})
        # Ensure default is empty dict, using single braces
        inputs = job.get("inputs", dict())
        
        # --- Phase Gating Check ---
        phase = meta.get("phase")
        run_id = meta.get("run_id", "default")
        
        if phase:
            # Check if we can run this phase
            if not self.gate.can_run(run_id, str(phase)):
                logger.info(f"Phase {phase} gated for run {run_id}. Requeueing with delay.")
                self.queue.requeue(job, delay=10000) # Check again in 10s
                return

        # --- Adaptive Batch Sizing ---
        # Allow override from meta
        if "batch_size" in meta:
             batch_size = int(meta["batch_size"])
        else:
             batch_size = self.sizer.get_batch_size()
        
        self.jobs_processed_session += 1
        console.print(f"[blue]Starting job #{self.jobs_processed_session}:[/blue] {workflow} [dim](Batch: {batch_size})[/dim]")
        
        start_time = time.time()
        status = "unknown"
        error_msg = None
        
        try:
            # We enforce a safe port for CLI execution to avoid conflicts with the main instance
            safe_env = {
                "N8N_PORT": "5679",
                "BATCH_SIZE": str(batch_size),
                "N8N_BATCH_SIZE": str(batch_size)
            }
            
            res = ""
            if mode == 'id':
                res = self.operator.execute_workflow(workflow_id=workflow, env=safe_env, broker_port=self.broker_port)
            else:
                res = self.operator.execute_workflow(file_path=workflow, env=safe_env, broker_port=self.broker_port)
            
            # Check for failure string from operator
            if res.startswith("Execution failed"):
                raise RuntimeError(res)

            logger.info(f"Execution started/result: {res}")
            status = "success"
            
        except Exception as e:
            status = "failed"
            error_msg = str(e)
            logger.error(f"Failed to execute job {workflow}: {e}")
            
            # Backoff Retry Logic
            retries = job.get("retries", 0)
            max_retries = 5
            if retries < max_retries:
                job["retries"] = retries + 1
                # Exponential backoff: 2s, 4s, 8s, 16s, 32s
                delay = 2000 * (2 ** retries) 
                logger.warning(f"Requeueing job {workflow} (Retry {job['retries']}/{max_retries}) in {delay}ms.")
                self.queue.requeue(job, delay=delay)
            else:
                logger.error(f"Job {workflow} failed max retries. Dropping.")

        finally:
            # --- Update Stats ---
            duration_ms = (time.time() - start_time) * 1000
            self.sizer.update_stats(duration_ms, success=(status == "success"))

            # Structured Logging
            log_entry = {
                "timestamp": start_time,
                "workflow": workflow,
                "status": status,
                "duration": duration_ms / 1000.0,
                "error": error_msg,
                "meta": meta,
                "retries": job.get("retries", 0),
                "batch_size": batch_size
            }
            
            try:
                with open(self.job_log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry) + "\n")
            except Exception as e:
                logger.error(f"Failed to write job log: {e}")