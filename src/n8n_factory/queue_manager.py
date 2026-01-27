import json
from typing import Optional, Dict, Any, List
from .operator import SystemOperator
from .logger import logger

class QueueManager:
    QUEUE_KEY = "n8n_factory:job_queue"

    def __init__(self, operator: Optional[SystemOperator] = None):
        self.operator = operator or SystemOperator()

    def enqueue(self, workflow: str, inputs: Dict[str, Any] = {}, mode: str = "id") -> str:
        """
        Adds a job to the queue.
        mode: 'id' or 'file'
        """
        job = {
            "workflow": workflow,
            "mode": mode,
            "inputs": inputs,
            "timestamp": None # Could add timestamp
        }
        payload = json.dumps(job)
        # Use list args to avoid shell splitting issues with JSON
        res = self.operator.inspect_redis(["LPUSH", self.QUEUE_KEY, payload])
        logger.info(f"Enqueued job for workflow '{workflow}'. Queue depth: {res}")
        return res

    def dequeue(self) -> Optional[Dict[str, Any]]:
        """
        Removes and returns the next job from the queue.
        """
        # RPOP returns the element or nothing
        res = self.operator.inspect_redis(["RPOP", self.QUEUE_KEY])
        if not res or res.strip() == "":
            return None
        
        try:
            return json.loads(res)
        except json.JSONDecodeError:
            logger.error(f"Failed to decode job from queue: {res}")
            return None

    def size(self) -> int:
        res = self.operator.inspect_redis(["LLEN", self.QUEUE_KEY])
        try:
            return int(res)
        except ValueError:
            return 0

    def clear(self):
        self.operator.inspect_redis(["DEL", self.QUEUE_KEY])

    def list_jobs(self, limit: int = 10) -> List[Dict[str, Any]]:
        # LRANGE key 0 limit-1
        res = self.operator.inspect_redis(["LRANGE", self.QUEUE_KEY, "0", str(limit - 1)])
        # redis-cli returns list items separated by newlines
        jobs = []
        for line in res.splitlines():
            try:
                if line.strip():
                    jobs.append(json.loads(line))
            except json.JSONDecodeError:
                pass
        return jobs
