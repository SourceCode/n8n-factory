import abc
import json
import time
from typing import Dict, Any, List, Optional
from ..ai.ollama_client import OllamaClient
from ..workspace.manager import WorkspaceManager
from ..state.store import StateStore
from ..verify.runner import VerificationRunner
from ..logger import logger

class BaseLoop(abc.ABC):
    def __init__(self, workspace: WorkspaceManager, config: Dict[str, Any], goal: str = "", resume: bool = False):
        self.workspace = workspace
        self.config = config
        self.goal = goal
        self.state_store = StateStore(workspace.state_file)
        self.state = {}
        
        # Initialize components
        self.llm = OllamaClient(
            model=config.get("model", "qwen3:8b"),
            base_url=config.get("ollama_url", "http://localhost:11434"),
            timeout=config.get("timeouts", {}).get("model_seconds", 120)
        )
        
        self.verifier = VerificationRunner(
            commands=config.get("verification", {}),
            timeout=config.get("timeouts", {}).get("verify_seconds", 600)
        )
        
        if resume:
            self.load_state()
        else:
            self.state = {
                "iteration": 0,
                "goal": goal,
                "history": [],
                "status": "initialized"
            }

    def load_state(self):
        self.state = self.state_store.load()
        if not self.state:
            logger.warning("No state found to resume. Starting fresh.")
            self.state = {"iteration": 0, "goal": self.goal, "history": [], "status": "initialized"}
        else:
            logger.info(f"Resumed loop at iteration {self.state.get('iteration')}")

    def save_state(self):
        self.state_store.save(self.state)

    def run(self, max_iterations: int = 25, approve: bool = False):
        """Main loop execution."""
        logger.info(f"Starting loop: {self.__class__.__name__}")
        
        while self.state["iteration"] < max_iterations:
            self.state["iteration"] += 1
            iter_num = self.state["iteration"]
            logger.info(f"--- Iteration {iter_num} ---")
            
            # 1. Prepare Context
            context = self.prepare_context()
            
            # 2. Agent Turn
            try:
                response = self.agent_turn(context)
            except Exception as e:
                logger.error(f"Agent turn failed: {e}")
                break
                
            # 3. Parse Contract
            plan = self.parse_response(response)
            if not plan:
                logger.warning("Failed to parse agent response. Injecting dummy phrase.")
                # Logic to inject dummy phrase next turn would go here
                continue

            # 4. Approval (if requested)
            if approve:
                print(f"\nAgent Plan:\n{json.dumps(plan, indent=2)}")
                if input("Approve? (y/n): ").lower() != 'y':
                    logger.info("User rejected plan. Stopping.")
                    break

            # 5. Execute Actions
            execution_results = self.execute_plan(plan)
            
            # 6. Verify
            verification_results = self.verify_changes(plan)
            
            # 7. Update State
            self.update_history(plan, execution_results, verification_results)
            self.save_state()
            
            # 8. Check Termination
            if self.should_terminate(plan, verification_results):
                logger.info("Termination condition met.")
                break
                
        logger.info("Loop finished.")

    @abc.abstractmethod
    def prepare_context(self) -> List[Dict[str, str]]:
        """Constructs prompt messages for the LLM."""
        pass

    def agent_turn(self, messages: List[Dict[str, str]]) -> str:
        """Calls the LLM."""
        response = self.llm.chat(messages, json_mode=True)
        return response.get("content", "{}")

    def parse_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Parses the JSON response from the agent."""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from agent: {content}")
            return None

    @abc.abstractmethod
    def execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Executes the actions defined in the plan (file writes, etc)."""
        pass

    def verify_changes(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Runs verification commands."""
        results = {}
        # Default verification logic, can be overridden
        if "verification" in plan:
             # If agent specified specific verification commands (advanced)
             pass
        
        # Run configured standard checks if files changed
        if plan.get("files_to_change"):
            results["lint"] = self.verifier.run("lint")
            results["tests"] = self.verifier.run("tests")
            
        return results

    def update_history(self, plan: Dict[str, Any], exec_results: Dict[str, Any], verify_results: Dict[str, Any]):
        entry = {
            "timestamp": time.time(),
            "iteration": self.state["iteration"],
            "plan": plan,
            "execution": exec_results,
            "verification": verify_results
        }
        self.state["history"].append(entry)

    @abc.abstractmethod
    def should_terminate(self, plan: Dict[str, Any], verify_results: Dict[str, Any]) -> bool:
        pass
