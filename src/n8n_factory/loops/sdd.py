from typing import List, Dict, Any, Optional
from .base import BaseLoop
from ..logger import logger

class SDDLoop(BaseLoop):
    SYSTEM_PROMPT = """You are an expert software engineer and agent using Spec-Driven Development (SDD).
Your goal is to satisfy the requirements in PLANNING.md by iteratively building and verifying.

    You operate on two files:
    1. PLANNING.md: Requirements, Acceptance Criteria, and Task List.
    2. BUILDING.md: Implementation Log, Decisions, and Verification Results.

    LOOP PROTOCOL:
    1. Read the current files.
    2. If PLANNING.md is empty or incomplete, your first step is to generate it.
    3. Pick the next uncompleted task from PLANNING.md.
    4. Implement the changes required.
    5. Record your progress in BUILDING.md.

    OUTPUT FORMAT:
    You must respond with valid JSON strictly matching this schema:
    {
      "intent": "plan | patch | verify",
      "rationale": "Explanation of your action",
      "planning_md_update": "Full content of PLANNING.md if changed, else null",
      "building_md_update": "Content to APPEND to BUILDING.md (log entry), or null",
      "files_to_create": [ {"path": "filename", "content": "file content"} ],
      "files_to_patch": [ {"path": "filename", "original_snippet": "...", "new_snippet": "..."} ],
      "verification_commands": ["cmd1", "cmd2"],
      "task_completed": "task_id_or_description_if_done",
      "finished": boolean
    }
    """

    def prepare_context(self) -> List[Dict[str, str]]:
        planning_content = self.workspace.read_file("PLANNING.md")
        building_content = self.workspace.read_file("BUILDING.md")
        
        # Simple context assembly
        user_msg = f"""
Current Goal: {self.goal}
Current Iteration: {self.state['iteration']}

--- CONTENT OF PLANNING.md ---
{planning_content}
------------------------------

--- CONTENT OF BUILDING.md (Last 1000 chars) ---
{building_content[-1000:]}
--------------------------------

Determine the next step. If PLANNING.md needs work, update it. If ready to build, implement the next task.
"""
        return [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_msg}
        ]

    def execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        results = {"files_written": [], "errors": []}
        
        # Update Meta Docs
        if plan.get("planning_md_update"):
            self.workspace.write_file("PLANNING.md", plan["planning_md_update"])
            results["files_written"].append("PLANNING.md")
            
        if plan.get("building_md_update"):
            current = self.workspace.read_file("BUILDING.md")
            new_content = current + "\n" + plan["building_md_update"]
            self.workspace.write_file("BUILDING.md", new_content)
            results["files_written"].append("BUILDING.md")

        # Create Files
        for f in plan.get("files_to_create", []):
            try:
                self.workspace.write_file(f["path"], f["content"])
                results["files_written"].append(f["path"])
            except Exception as e:
                results["errors"].append(f"Failed to write {f['path']}: {e}")

        # Patch Files (Simple replacement for now, full patching is complex)
        for f in plan.get("files_to_patch", []):
            try:
                content = self.workspace.read_file(f["path"])
                if f["original_snippet"] in content:
                    new_content = content.replace(f["original_snippet"], f["new_snippet"])
                    self.workspace.write_file(f["path"], new_content)
                    results["files_written"].append(f["path"])
                else:
                    results["errors"].append(f"Patch failed for {f['path']}: Original snippet not found.")
            except Exception as e:
                results["errors"].append(f"Failed to patch {f['path']}: {e}")

        return results

    def should_terminate(self, plan: Dict[str, Any], verify_results: Dict[str, Any]) -> bool:
        return plan.get("finished", False)
