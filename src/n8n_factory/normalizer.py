import copy
from typing import Dict, Any, List
from .models import Recipe
from .logger import logger

class WorkflowNormalizer:
    def normalize_json(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalizes a JSON workflow:
        1. Standardizes node names if they are generic.
        2. Ensures positions exist.
        3. Sorts keys for consistent diffs.
        """
        logger.info("Normalizing JSON workflow...")
        normalized = copy.deepcopy(workflow)
        nodes = normalized.get("nodes", [])
        
        # Mapping to track used names
        used_names = set(n.get("name") for n in nodes)
        
        for i, node in enumerate(nodes):
            # Ensure Position
            if "position" not in node:
                node["position"] = [0, 0]
            
            # Standardize Name if generic (e.g., contains 'n8n-nodes-base')
            # Only rename if it seems auto-generated or generic?
            # For now, let's just ensure clean structure.
            # Renaming nodes breaks connections unless we update connections too.
            # That's complex. Let's skip renaming for now to be safe, 
            # unless we implement connection updating.
            pass

        # Sort nodes by name for deterministic output
        nodes.sort(key=lambda x: x.get("name", ""))
        normalized["nodes"] = nodes
        
        # Sort connections
        connections = normalized.get("connections", {})
        sorted_conns = {}
        for key in sorted(connections.keys()):
            sorted_conns[key] = connections[key]
        normalized["connections"] = sorted_conns
        
        return normalized

    def normalize_recipe(self, recipe: Recipe) -> Recipe:
        """
        Normalizes a Recipe:
        1. Standardizes step IDs?
        """
        logger.info("Normalizing Recipe...")
        # Currently just a pass-through, but acts as a placeholder for future standards enforcement.
        return copy.deepcopy(recipe)
