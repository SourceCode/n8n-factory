import json
import time
from typing import Optional, Dict, Any, List
from .operator import SystemOperator
from .logger import logger

class QueueManager:
    QUEUE_KEY = "n8n_factory:job_queue"
    DELAYED_KEY = "n8n_factory:job_queue:delayed"
    CURSORS_KEY_PREFIX = "n8n_factory:cursors"

    def __init__(self, operator: Optional[SystemOperator] = None):
        self.operator = operator or SystemOperator()

    def enqueue(self, workflow: str, inputs: Dict[str, Any] = {}, mode: str = "id", meta: Dict[str, Any] = {}, delay: int = 0) -> str:
        """
        Adds a job to the queue.
        mode: 'id' or 'file'
        delay: delay in milliseconds before the job becomes available
        """
        job = {
            "workflow": workflow,
            "mode": mode,
            "inputs": inputs,
            "meta": meta,
            "timestamp": time.time(),
            "retries": 0
        }
        payload = json.dumps(job)
        
        if delay > 0:
            ready_time = (time.time() * 1000) + delay
            # Use ZADD for delayed queue
            res = self.operator.inspect_redis(["ZADD", self.DELAYED_KEY, str(ready_time), payload])
            logger.info(f"Enqueued delayed job for workflow '{workflow}' (Delay: {delay}ms).")
        else:
            # Use list args to avoid shell splitting issues with JSON
            res = self.operator.inspect_redis(["LPUSH", self.QUEUE_KEY, payload])
            logger.info(f"Enqueued job for workflow '{workflow}'. Queue depth: {res}")
            
        return res

    def requeue(self, job: Dict[str, Any], delay: int = 0):
        """
        Pushes a job back onto the queue (e.g. after failure).
        """
        if delay > 0:
            ready_time = (time.time() * 1000) + delay
            payload = json.dumps(job)
            res = self.operator.inspect_redis(["ZADD", self.DELAYED_KEY, str(ready_time), payload])
            logger.warning(f"Requeued job for workflow '{job.get('workflow')}' with delay {delay}ms.")
            return res
        else:
            payload = json.dumps(job)
            res = self.operator.inspect_redis(["LPUSH", self.QUEUE_KEY, payload])
            logger.warning(f"Requeued job for workflow '{job.get('workflow')}'. Queue depth: {res}")
            return res

    def dequeue(self) -> Optional[Dict[str, Any]]:
        """
        Removes and returns the next job from the queue.
        Checks delayed queue first for ready jobs.
        """
        # 1. Check delayed queue for jobs ready now
        now = time.time() * 1000
        # ZRANGEBYSCORE key -inf now LIMIT 0 1
        res = self.operator.inspect_redis(["ZRANGEBYSCORE", self.DELAYED_KEY, "-inf", str(now), "LIMIT", "0", "1"])
        
        # If we got a delayed job, try to remove it (atomically ideally, but here distinct steps)
        # Note: In a high-concurrency env, this race condition (read-then-remove) could be an issue.
        # Ideally we use a Lua script. For this factory tool, we assume single scheduler or low contention.
        if res and res.strip():
            # Redis CLI might return list with one item
            payload = res.strip()
            # Remove it
            rem_res = self.operator.inspect_redis(["ZREM", self.DELAYED_KEY, payload])
            if rem_res and int(rem_res) > 0:
                try:
                    return json.loads(payload)
                except json.JSONDecodeError:
                    logger.error(f"Failed to decode delayed job: {payload}")

        # 2. Regular queue
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
            
    def delayed_size(self) -> int:
        res = self.operator.inspect_redis(["ZCARD", self.DELAYED_KEY])
        try:
            return int(res)
        except ValueError:
            return 0

    def clear(self):
        self.operator.inspect_redis(["DEL", self.QUEUE_KEY])
        self.operator.inspect_redis(["DEL", self.DELAYED_KEY])

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

    # Cursor Management
    
    def _get_cursor_key(self, run_id: str) -> str:
        return f"{self.CURSORS_KEY_PREFIX}:{run_id}"

    def set_cursor(self, run_id: str, cursor: str, value: Any):
        """Sets a cursor value for a specific run."""
        key = self._get_cursor_key(run_id)
        self.operator.inspect_redis(["HSET", key, cursor, str(value)])

    def get_cursor(self, run_id: str, cursor: str) -> Optional[str]:
        """Gets a cursor value."""
        key = self._get_cursor_key(run_id)
        res = self.operator.inspect_redis(["HGET", key, cursor])
        return res if res and res.strip() else None
        
    def get_all_cursors(self, run_id: str) -> Dict[str, str]:
        """Gets all cursors for a run."""
        key = self._get_cursor_key(run_id)
        res = self.operator.inspect_redis(["HGETALL", key])
        # Redis CLI HGETALL returns key\nval\nkey\nval...
        lines = res.splitlines()
        result = {}
        for i in range(0, len(lines), 2):
            if i + 1 < len(lines):
                result[lines[i]] = lines[i+1]
        return result

    def reset_cursors(self, run_id: str):
        """Clears all cursors for a run."""
        key = self._get_cursor_key(run_id)
        self.operator.inspect_redis(["DEL", key])
