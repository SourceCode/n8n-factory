import os
import json
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, List

class WorkspaceManager:
    DIR_NAME = ".n8n-factory"
    
    def __init__(self, root: str = "."):
        self.root = Path(root).resolve()
        self.factory_dir = self.root / self.DIR_NAME
        self.state_file = self.factory_dir / "state.json"
        self.logs_dir = self.factory_dir / "logs"
        self.summaries_dir = self.factory_dir / "summaries"
        self.patches_dir = self.factory_dir / "patches"
        self.context_dir = self.factory_dir / "context"

    def init_workspace(self):
        """Creates the necessary directory structure."""
        self.factory_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        self.summaries_dir.mkdir(exist_ok=True)
        self.patches_dir.mkdir(exist_ok=True)
        self.context_dir.mkdir(exist_ok=True)
        
        # Create default config if not exists
        config_path = self.root / "loop.config.yaml"
        if not config_path.exists():
            default_config = {
                "model": "qwen3:8b",
                "backend": "ollama",
                "max_iterations": 25,
                "verification": {
                    "lint": "echo 'No lint command configured'",
                    "tests": "echo 'No test command configured'"
                },
                "timeouts": {
                    "model_seconds": 120,
                    "verify_seconds": 600
                }
            }
            with open(config_path, "w") as f:
                yaml.dump(default_config, f, sort_keys=False)

    def load_config(self) -> Dict[str, Any]:
        config_path = self.root / "loop.config.yaml"
        if config_path.exists():
            with open(config_path, "r") as f:
                return yaml.safe_load(f) or {{}}
        return {{}}

    def ensure_sdd_files(self):
        """Ensures PLANNING.md and BUILDING.md exist."""
        planning = self.root / "PLANNING.md"
        building = self.root / "BUILDING.md"
        
        if not planning.exists():
            planning.write_text("# Planning\n\n## Problem Statement\n\n## Tasks\n- [ ] Initial Task", encoding="utf-8")
        
        if not building.exists():
            building.write_text("# Building Log\n\n", encoding="utf-8")

    def ensure_kanban_file(self):
        kanban = self.root / "KANBAN.md"
        if not kanban.exists():
            kanban.write_text("## To Do\n\n- [ ] Task 1\n\n## Doing\n\n## Done\n", encoding="utf-8")

    def read_file(self, filename: str) -> str:
        path = self.root / filename
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    def write_file(self, filename: str, content: str):
        path = self.root / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def list_files(self, pattern: str = "**/*") -> List[str]:
        # Simple glob wrapper, excludes .git and factory dir
        files = []
        for p in self.root.glob(pattern):
            if p.is_file() and ".git" not in p.parts and self.DIR_NAME not in p.parts:
                files.append(str(p.relative_to(self.root)))
        return files
