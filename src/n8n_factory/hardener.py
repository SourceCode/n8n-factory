import copy
from typing import Dict, Any, List
from .models import Recipe, RecipeStep
from .logger import logger

class WorkflowHardener:
    def harden_json(self, workflow: Dict[str, Any], add_logging: bool = False, add_error_trigger: bool = False) -> Dict[str, Any]:
        """
        Hardens a JSON workflow.
        """
        logger.info(f"Hardening JSON workflow (logging={add_logging}, error_trigger={add_error_trigger})...")
        hardened = copy.deepcopy(workflow)
        nodes = hardened.get("nodes", [])
        connections = hardened.get("connections", {})
        
        if add_logging:
            # Find Start Node
            start_node = next((n for n in nodes if "start" in n.get("type", "").lower() or "trigger" in n.get("type", "").lower()), None)
            
            if start_node:
                start_name = start_node["name"]
                logger_name = f"Logger_{start_name}"
                
                # Create Logger Node (Manual construction as we don't have the TemplateLoader here easily, or we hardcode)
                logger_node = {
                    "parameters": {
                        "jsCode": f"// DEBUG NODE\nconsole.log('DEBUG [{start_name}]:', items);\nreturn items;"
                    },
                    "name": logger_name,
                    "type": "n8n-nodes-base.code",
                    "typeVersion": 2,
                    "position": [
                        start_node["position"][0] + 100,
                        start_node["position"][1]
                    ]
                }
                nodes.append(logger_node)
                
                # Insert Logger into flow: Start -> Logger -> (Original Next Nodes)
                if start_name in connections and "main" in connections[start_name]:
                    # Move Start's outgoing connections to Logger
                    outgoing = connections[start_name]["main"]
                    if logger_name not in connections: connections[logger_name] = {}
                    connections[logger_name]["main"] = outgoing
                    
                # Connect Start -> Logger
                connections[start_name] = {
                    "main": [[{"node": logger_name, "type": "main", "index": 0}]]
                }
                logger.info(f"Injected logger after node '{start_name}'")

        if add_error_trigger:
            # Check if Error Trigger exists
            if not any(n.get("type") == "n8n-nodes-base.errorTrigger" for n in nodes):
                error_node = {
                    "parameters": {},
                    "name": "Error Trigger",
                    "type": "n8n-nodes-base.errorTrigger",
                    "typeVersion": 1,
                    "position": [0, 400]
                }
                nodes.append(error_node)
                
                # Add a Logger connected to it
                error_logger = {
                    "parameters": {
                         "jsCode": "console.error('WORKFLOW ERROR:', items[0].json);\nreturn items;"
                    },
                    "name": "Error Logger",
                    "type": "n8n-nodes-base.code",
                    "typeVersion": 2,
                    "position": [200, 400]
                }
                nodes.append(error_logger)
                
                connections["Error Trigger"] = {
                    "main": [[{"node": "Error Logger", "type": "main", "index": 0}]]
                }
                logger.info("Added Error Trigger and Error Logger.")

        return hardened

    def harden_recipe(self, recipe: Recipe, add_logging: bool = False, add_error_trigger: bool = False) -> Recipe:
        logger.info(f"Hardening Recipe (logging={add_logging}, error_trigger={add_error_trigger})...")
        hardened = copy.deepcopy(recipe)
        
        if add_logging:
            new_steps = []
            for step in hardened.steps:
                new_steps.append(step)
                # Naive injection: Add a logger after every step? No, too noisy.
                # Just start? 
                # Let's add a logger after the first step for now.
                # Implementing graph insertion in a linear list is tricky without re-linking IDs.
                # For Recipe, simple "Debug" flag on step is better.
                # Enable debug on all steps?
                step.debug = True
            logger.info("Enabled debug mode on all steps.")
        
        return hardened
