import json
import time
from typing import Dict, Any, Optional
from pathlib import Path
from ..logger import logger

class StateStore:
    def __init__(self, state_path: Path):
        self.state_path = state_path

    def load(self) -> Dict[str, Any]:
        if self.state_path.exists():
            try:
                with open(self.state_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
        return {}

    def save(self, state: Dict[str, Any]):
        try:
            state["_updated_at"] = time.time()
            with open(self.state_path, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
