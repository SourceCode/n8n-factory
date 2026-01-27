from typing import List, Dict, Any
from .base import BaseLoop
from ..logger import logger

class KanbanLoop(BaseLoop):
    SYSTEM_PROMPT = """You are a Kanban Workflow Agent.
Your job is to manage the board in KANBAN.md.
1. Read the board.
2. If there are items in 'Doing', continue working on them.
3. If 'Doing' is empty, move the top item from 'To Do' to 'Doing'.
4. Perform the work (generate code, configs, etc.).
5. When work is verified, move item to 'Done'.

OUTPUT FORMAT (JSON):
{
  "intent": "move_card | work | finish_card",
  "kanban_md_update": "Full content of KANBAN.md",
  "files_to_create": [],
  "rationale": "..."
}
"""
    
    def prepare_context(self) -> List[Dict[str, str]]:
        kanban_content = self.workspace.read_file("KANBAN.md")
        return [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"Current Board:\n{kanban_content}\n\nProceed."}
        ]

    def execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        results = {"files_written": []}
        
        if plan.get("kanban_md_update"):
            self.workspace.write_file("KANBAN.md", plan["kanban_md_update"])
            results["files_written"].append("KANBAN.md")
            
        # Basic file handling inherited from logic or duplicated. 
        # For a full implementation, we'd share the FileOperation logic.
        for f in plan.get("files_to_create", []):
            self.workspace.write_file(f["path"], f["content"])
            results["files_written"].append(f["path"])
            
        return results

    def should_terminate(self, plan: Dict[str, Any], verify_results: Dict[str, Any]) -> bool:
        # Kanban runs until stopped or empty (logic can be improved)
        return False
