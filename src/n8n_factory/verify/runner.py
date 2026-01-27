import subprocess
import time
from typing import Dict, Any, List, Optional
from ..logger import logger

class VerificationRunner:
    def __init__(self, commands: Dict[str, str], timeout: int = 600):
        self.commands = commands
        self.timeout = timeout

    def run(self, command_key: str) -> Dict[str, Any]:
        """Runs a named command from the config."""
        cmd_str = self.commands.get(command_key)
        if not cmd_str:
            return {"success": True, "output": f"No command configured for '{command_key}'. Skipped.", "exit_code": 0}

        return self.run_shell(cmd_str)

    def run_shell(self, cmd_str: str) -> Dict[str, Any]:
        logger.info(f"Verifying: {cmd_str}")
        start_time = time.time()
        
        try:
            # Using shell=True for flexibility with pipes/redirects defined in config
            result = subprocess.run(
                cmd_str, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=self.timeout
            )
            duration = time.time() - start_time
            
            return {
                "success": result.returncode == 0,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": duration,
                "command": cmd_str
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Command timed out after {self.timeout}s",
                "duration": self.timeout,
                "command": cmd_str
            }
        except Exception as e:
             return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "duration": time.time() - start_time,
                "command": cmd_str
            }
