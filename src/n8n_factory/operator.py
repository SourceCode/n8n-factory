import subprocess
import json
import logging
from typing import List, Dict, Any, Optional, Union

logger = logging.getLogger("n8n_factory")

class SystemOperator:
    def __init__(self, n8n_container: Optional[str] = None, db_container: Optional[str] = None, redis_container: Optional[str] = None):
        import os
        self.n8n_container = n8n_container or os.getenv("N8N_CONTAINER_NAME", "n8n")
        self.db_container = db_container or os.getenv("DB_CONTAINER_NAME", "postgres")
        # Default changed to n8n-redis as per requirements, adjustable via env or init arg
        self.redis_container = redis_container or os.getenv("REDIS_CONTAINER_NAME", "n8n-redis")

    def _run_cmd(self, cmd: List[str]) -> str:
        try:
            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.strip() if e.stderr else str(e)
            logger.error(f"Command failed: {err_msg}")
            raise RuntimeError(f"Command failed: {err_msg}")
        except FileNotFoundError:
             logger.error("Command not found (is Docker installed?)")
             raise RuntimeError("Docker command not found.")

    def get_logs(self, service: str, tail: int = 100) -> str:
        """
        Fetches logs from a service container.
        """
        container = getattr(self, f"{service}_container", service)
        try:
            return self._run_cmd(["docker", "logs", "--tail", str(tail), container])
        except RuntimeError:
            return f"Failed to get logs for {service} (container: {container})"

    def run_db_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Executes a SQL query against the n8n Postgres database and returns JSON-friendly dicts.
        """
        # Wrapping query to force JSON output per row
        full_query = f"COPY (SELECT row_to_json(t) FROM ({query}) t) TO STDOUT;"
        
        # User defaults: postgres user, n8n db. 
        # Ideally configurable, but standard for n8n docker stacks.
        cmd = [
            "docker", "exec", self.db_container,
            "psql", "-U", "postgres", "-d", "n8n", "-c", full_query
        ]
        
        try:
            output = self._run_cmd(cmd)
            results = []
            for line in output.splitlines():
                if line.strip():
                    try:
                        results.append(json.loads(line))
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse JSON line from DB: {line}")
            return results
        except RuntimeError as e:
            logger.error(f"DB Query failed: {e}")
            return []

    def inspect_redis(self, command: Union[str, List[str]]) -> str:
        """
        Runs a redis-cli command.
        Accepts a string (space-separated) or a list of arguments (safer for data).
        """
        import os
        redis_args = command.split() if isinstance(command, str) else command
        
        # Inject Auth if present
        redis_password = os.getenv("REDIS_PASSWORD")
        auth_args = ["-a", redis_password] if redis_password else []
        
        cmd = ["docker", "exec", self.redis_container, "redis-cli"] + auth_args + redis_args
        try:
            return self._run_cmd(cmd)
        except RuntimeError as e:
             return f"Redis command failed: {e}"

    def execute_workflow(self, workflow_id: Optional[str] = None, file_path: Optional[str] = None, env: Dict[str, str] = {}, broker_port: Optional[int] = None) -> str:
        """
        Executes an n8n workflow.
        """
        import os
        env_args = []
        
        # Merge broker port into env if provided or found in system env
        target_broker_port = broker_port or os.getenv("N8N_RUNNERS_BROKER_PORT")
        if target_broker_port:
            env["N8N_RUNNERS_BROKER_PORT"] = str(target_broker_port)

        for k, v in env.items():
            env_args.extend(["-e", f"{k}={v}"])

        if workflow_id:
             # Execute by ID in container
             cmd = ["docker", "exec"] + env_args + ["-u", "node", self.n8n_container, "n8n", "execute", "--id", workflow_id]
        elif file_path:
             # Execute by file. 
             # Challenge: File needs to be IN the container.
             # workaround: cat file | docker exec ...
             # n8n execute --file <file> reads from filesystem.
             # We can try passing via stdin if n8n supports it? No.
             # We must `docker cp` it first to a temp loc.
             
             container_tmp = "/tmp/exec_workflow.json"
             cp_cmd = ["docker", "cp", file_path, f"{self.n8n_container}:{container_tmp}"]
             self._run_cmd(cp_cmd)
             
             cmd = ["docker", "exec"] + env_args + ["-u", "node", self.n8n_container, "n8n", "execute", "--file", container_tmp]
        else:
            raise ValueError("Must provide workflow_id or file_path")

        try:
            return self._run_cmd(cmd)
        except RuntimeError as e:
            return f"Execution failed: {e}"

    def trigger_webhook(self, method: str, url: str, data: Dict[str, Any] = {}) -> str:
        """
        Triggers a webhook using curl from inside the n8n container.
        """
        payload = json.dumps(data)
        cmd = [
            "docker", "exec", self.n8n_container, 
            "curl", "-s", "-X", method, 
            "-H", "Content-Type: application/json", 
            "-d", payload, 
            url
        ]
        try:
            return self._run_cmd(cmd)
        except RuntimeError as e:
            return f"Webhook trigger failed: {e}"

    def analyze_logs(self, service: str = "n8n", hours: int = 1) -> Dict[str, Any]:
        """
        Analyzes recent logs for errors.
        """
        logs = self.get_logs(service, tail=2000)
        
        error_count = logs.count("ERROR")
        warn_count = logs.count("WARN")
        crashed = logs.count("crashed")
        
        return {
            "service": service,
            "analysis_window_tail": 2000,
            "errors": error_count,
            "warnings": warn_count,
            "crashes_detected": crashed > 0,
            "status": "Healthy" if error_count == 0 and not crashed else "Unhealthy"
        }

    def get_active_executions(self) -> List[Dict[str, Any]]:
        """
        Fetches currently running executions from the database.
        """
        query = """
            SELECT e.id, e."workflowId", w.name, e.status, e."startedAt", e.mode 
            FROM execution_entity e 
            LEFT JOIN workflow_entity w ON e."workflowId" = w.id 
            WHERE e.status = 'running' 
            ORDER BY e."startedAt" DESC
        """
        return self.run_db_query(query)

    def get_execution_details(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetches status and basic details for a specific execution.
        Note: We avoid fetching the full 'data' blob here if possible to keep it light, 
        unless we need to inspect specific node progress.
        For progress monitoring, we often need 'data'.
        """
        query = f"""
            SELECT e.id, e."workflowId", w.name, e.status, e."startedAt", e.mode, e.data
            FROM execution_entity e
            LEFT JOIN workflow_entity w ON e."workflowId" = w.id
            WHERE e.id = '{execution_id}'
        """
        results = self.run_db_query(query)
        return results[0] if results else None
