import json
import time
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
        # Check dependency cursor
        # Key convention: n8n_factory:cursors:<run_id>
        # Fields: <phase>_current, <phase>_total
        
        cursor_key = f"n8n_factory:cursors:{run_id}"
        
        # We need current and total for the dependency phase
        # Assuming keys like "phase_2_current" and "phase_2_total"
        # The user might name phases arbitrarily, but we assume strict naming for now or config match.
        
        dep_current_field = f"{dep_phase}_current"
        dep_total_field = f"{dep_phase}_total"
        
        # Fetch both
        vals = self.operator.inspect_redis(["HMGET", cursor_key, dep_current_field, dep_total_field])
        if not vals:
            return False
            
        lines = vals.splitlines()
        # redis-cli returns lines. if items are missing they might be empty strings or nil
        # Using HMGET with cli usually returns values on separate lines.
        
        try:
            current_val = int(lines[0]) if len(lines) > 0 and lines[0].strip() else 0
            total_val = int(lines[1]) if len(lines) > 1 and lines[1].strip() else 0
        except (ValueError, IndexError):
            # If total is unknown, we can't gate properly, assume closed?
            # Or assume open if we haven't started?
            # Safer to assume closed if rule exists but data missing.
            return False
            
        if rule.get("condition") == "complete":
            # Complete means current >= total
            # Also require total > 0 to ensure it actually started/initialized
            if total_val > 0 and current_val >= total_val:
                return True
            return False
            
        return True
