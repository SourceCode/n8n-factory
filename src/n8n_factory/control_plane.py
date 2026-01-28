import json
import time
import os
import subprocess
from typing import Optional, Dict, Any
from .operator import SystemOperator
from .logger import logger

class AdaptiveBatchSizer:
    KEY_CONFIG = "n8n_factory:config:batch_sizing"
    KEY_CURRENT = "n8n_factory:state:batch_size"
    
    def __init__(self, operator: SystemOperator, default_size: int = 10):
        self.operator = operator
        self.default_size = default_size
        self._ensure_config()

    def _ensure_config(self):
        """Ensures default config exists in Redis."""
        defaults = {
            "min_size": 1,
            "max_size": 100,
            "target_latency_ms": 5000, # 5 seconds per batch target
            "failure_threshold_rate": 0.1, # 10% failure rate triggers backoff
            "adjustment_factor": 1.2,
            "window_size": 10 # Number of jobs to average over
        }
        # Set if not exists (NX)
        self.operator.inspect_redis(["SET", self.KEY_CONFIG, json.dumps(defaults), "NX"])
        self.operator.inspect_redis(["SET", self.KEY_CURRENT, str(self.default_size), "NX"])

    def get_batch_size(self) -> int:
        res = self.operator.inspect_redis(["GET", self.KEY_CURRENT])
        try:
            return int(res)
        except (ValueError, TypeError):
            return self.default_size

    def get_config(self) -> Dict[str, Any]:
        res = self.operator.inspect_redis(["GET", self.KEY_CONFIG])
        try:
            return json.loads(res)
        except (TypeError, json.JSONDecodeError):
            return {}

    def update_stats(self, duration_ms: float, success: bool):
        """
        Called by scheduler after a job. Updates moving averages and adjusts batch size.
        """
        # We'll use a simple atomic update script or just read/write for now.
        # Ideally, we should store a list of recent stats in Redis to be stateless.
        
        # 1. Push stat to a list
        stat = json.dumps({"d": duration_ms, "s": int(success)})
        key_stats = "n8n_factory:stats:recent_jobs"
        
        config = self.get_config()
        window = config.get("window_size", 10)
        
        self.operator.inspect_redis(["LPUSH", key_stats, stat])
        self.operator.inspect_redis(["LTRIM", key_stats, "0", str(window - 1)])
        
        # 2. Check if we have enough data to decide
        # (Optimization: Only check every N jobs or probabilistic to save Redis calls)
        if time.time() % 5 < 0.5: # Simple throttle, or just do it every time if low volume
            self._recalculate(key_stats, config)

    def _recalculate(self, key_stats: str, config: Dict[str, Any]):
        # Get all stats
        items = self.operator.inspect_redis(["LRANGE", key_stats, "0", "-1"])
        if not items:
            return
            
        durations = []
        failures = 0
        
        try:
            lines = items.splitlines() if isinstance(items, str) else items
            for item in lines:
                if not item: continue
                data = json.loads(item)
                durations.append(data["d"])
                if data["s"] == 0:
                    failures += 1
        except Exception as e:
            logger.error(f"Error parsing stats: {e}")
            return

        if not durations:
            return

        avg_latency = sum(durations) / len(durations)
        failure_rate = failures / len(durations)
        
        current_size = self.get_batch_size()
        new_size = current_size
        
        # Logic
        target = config.get("target_latency_ms", 5000)
        max_size = config.get("max_size", 50)
        min_size = config.get("min_size", 1)
        factor = config.get("adjustment_factor", 1.2)
        
        if failure_rate > config.get("failure_threshold_rate", 0.1):
            # High failure -> slash batch size
            new_size = max(min_size, int(current_size / factor))
            logger.warning(f"High failure rate ({failure_rate:.2f}). Reducing batch size to {new_size}.")
        
        elif avg_latency > target * 1.2:
            # Too slow -> reduce
            new_size = max(min_size, int(current_size / factor))
            logger.info(f"Latency high ({avg_latency:.0f}ms > {target}ms). Reducing batch size to {new_size}.")
            
        elif avg_latency < target * 0.8:
            # Too fast -> increase
            new_size = min(max_size, int(current_size * factor) + 1)
            # logger.info(f"Latency low ({avg_latency:.0f}ms). Increasing batch size to {new_size}.")
            
        if new_size != current_size:
            self.operator.inspect_redis(["SET", self.KEY_CURRENT, str(new_size)])


class PhaseGate:
    KEY_RULES = "n8n_factory:config:gates"
    FALLBACK_CURSOR_FILE = ".n8n-factory/cursors.json"
    
    def __init__(self, operator: SystemOperator):
        self.operator = operator

    def set_rule(self, phase: str, dependency: str, condition: str = "complete"):
        """
        Defines a rule: 'phase' cannot run until 'dependency' meets 'condition'.
        """
        # We store rules as a hash: phase -> json_rule
        rule = {"dependency": dependency, "condition": condition}
        self.operator.inspect_redis(["HSET", self.KEY_RULES, str(phase), json.dumps(rule)])

    def get_rule(self, phase: str) -> Optional[Dict[str, Any]]:
        res = self.operator.inspect_redis(["HGET", self.KEY_RULES, str(phase)])
        if res and res.strip():
            try:
                return json.loads(res)
            except:
                pass
        return None

    def can_run(self, run_id: str, phase: str) -> bool:
        """
        Checks if the phase is allowed to run for the given run_id.
        """
        rule = self.get_rule(phase)
        if not rule:
            return True # No rule = open
            
        dep_phase = rule.get("dependency")
        cursor_key = f"n8n_factory:cursors:{run_id}"
        dep_current_field = f"{dep_phase}_current"
        dep_total_field = f"{dep_phase}_total"
        
        # 1. Try Redis
        current_val, total_val = self._check_redis(cursor_key, dep_current_field, dep_total_field)
        
        # 2. Try File Fallback if Redis missed
        if current_val is None or total_val is None:
            current_val, total_val = self._check_file(run_id, dep_current_field, dep_total_field)

        # 3. Evaluate
        # Default to locked if data missing
        if current_val is None or total_val is None:
            return False
            
        if rule.get("condition") == "complete":
            # Complete means current >= total
            # Also require total > 0 to ensure it actually started/initialized
            if total_val > 0 and current_val >= total_val:
                return True
            return False
            
        return True

    def _check_redis(self, key, field_current, field_total):
        vals = self.operator.inspect_redis(["HMGET", key, field_current, field_total])
        if not vals:
            return None, None
        
        lines = vals.splitlines()
        try:
            c = int(lines[0]) if len(lines) > 0 and lines[0].strip() else None
            t = int(lines[1]) if len(lines) > 1 and lines[1].strip() else None
            return c, t
        except (ValueError, IndexError):
            return None, None

    def _check_file(self, run_id, field_current, field_total):
        if not os.path.exists(self.FALLBACK_CURSOR_FILE):
            return None, None
            
        try:
            with open(self.FALLBACK_CURSOR_FILE, 'r') as f:
                data = json.load(f)
                run_data = data.get(run_id, {})
                c = run_data.get(field_current)
                t = run_data.get(field_total)
                return c, t
        except Exception as e:
            logger.warning(f"Failed to read fallback cursor file: {e}")
            return None, None

class AutoRefiller:
    def __init__(self, operator: SystemOperator):
        self.operator = operator
        self.last_refill = 0
        self.cooldown = 10 # seconds

    def check_and_refill(self, current_size: int, threshold: int, command: str):
        if current_size < threshold:
            now = time.time()
            if now - self.last_refill > self.cooldown:
                logger.info(f"Queue size {current_size} < threshold {threshold}. Triggering refill.")
                self.last_refill = now
                try:
                    # Execute command in background or blocking? Blocking safer to avoid fork bombs.
                    # But we want the scheduler to keep running. Background preferable?
                    # "Add a native queue manager mode" implies the scheduler does this.
                    # Let's run blocking but with timeout, or background.
                    # subprocess.Popen matches typical "worker" patterns.
                    
                    # Split command string safely?
                    # Assuming command is a simple shell string
                    subprocess.Popen(command, shell=True)
                except Exception as e:
                    logger.error(f"Failed to trigger refill command: {e}")
