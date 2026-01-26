import copy
import re
from typing import List, Set, Dict, Any
from .models import Recipe, RecipeStep
from .logger import logger

class WorkflowOptimizer:
    def optimize(self, recipe: Recipe) -> Recipe:
        logger.debug(f"Starting optimization for recipe: {recipe.name}")
        optimized_recipe = copy.deepcopy(recipe)
        
        optimized_recipe.steps = self._merge_set_nodes(optimized_recipe.steps)
        optimized_recipe.steps = self._prune_passthrough(optimized_recipe.steps)
        optimized_recipe.steps = self._constant_folding(optimized_recipe.steps)
        
        self._analyze_unused_variables(optimized_recipe.steps)
        # Improvement #10: Description Audit
        self._audit_descriptions(optimized_recipe.steps, strict=recipe.strict)
        
        logger.debug("Optimization complete.")
        return optimized_recipe

    def refactor_json(self, workflow: Dict[str, Any], reinsert_edges: bool = False) -> Dict[str, Any]:
        """
        Refactors an existing n8n workflow JSON.
        Can remove and re-insert edges based on node order.
        """
        logger.debug(f"Starting JSON refactor. reinsert_edges={reinsert_edges}")
        
        refactored = copy.deepcopy(workflow)
        nodes = refactored.get("nodes", [])
        
        if reinsert_edges:
            logger.info("Removing existing connections...")
            refactored["connections"] = {}
            
            logger.info("Re-inserting edges based on node order...")
            connections = {}
            previous_node_name = None
            
            for i, node in enumerate(nodes):
                node_name = node.get("name")
                if not node_name:
                    logger.warning(f"Node at index {i} has no name. Skipping connection logic.")
                    continue
                
                logger.debug(f"Processing node {i}: {node_name} ({node.get('type')})")
                
                if previous_node_name:
                    # Logic: Connect previous main output to current main input
                    # NOTE: This assumes a simple linear flow. Complex branching is lost.
                    logger.debug(f"Connecting {previous_node_name} -> {node_name}")
                    
                    if previous_node_name not in connections:
                        connections[previous_node_name] = {}
                    
                    if "main" not in connections[previous_node_name]:
                        connections[previous_node_name]["main"] = []
                        
                    # Ensure list structure
                    while len(connections[previous_node_name]["main"]) <= 0:
                        connections[previous_node_name]["main"].append([])
                        
                    connections[previous_node_name]["main"][0].append({
                        "node": node_name,
                        "type": "main",
                        "index": 0
                    })
                
                # Check for disabled nodes if we want to skip them? 
                # For now, we connect through them or to them as they appear in the list.
                
                previous_node_name = node_name
                
            refactored["connections"] = connections
            logger.info(f"Rebuilt connections for {len(nodes)} nodes.")

        return refactored

    def _merge_set_nodes(self, steps: List[RecipeStep]) -> List[RecipeStep]:
        if not steps: return []
        new_steps = []
        i = 0
        while i < len(steps):
            current_step = steps[i]
            if current_step.template == "set":
                merged_params = [{"name": current_step.params["name"], "value": current_step.params["value"]}]
                j = i + 1
                while j < len(steps) and steps[j].template == "set":
                    merged_params.append({"name": steps[j].params["name"], "value": steps[j].params["value"]})
                    j += 1
                if len(merged_params) > 1:
                    logger.info(f"Optimizer: Merging {len(merged_params)} 'set' nodes.")
                    new_step = RecipeStep(
                        id=f"merged_set_{i}",
                        template="set_multi",
                        params={"items": merged_params},
                        description="Merged by Optimizer"
                    )
                    new_steps.append(new_step)
                    i = j 
                    continue
            new_steps.append(current_step)
            i += 1
        return new_steps

    def _prune_passthrough(self, steps: List[RecipeStep]) -> List[RecipeStep]:
        new_steps = []
        for step in steps:
            if step.template == "code" and not step.debug:
                code = step.params.get("code", "").strip()
                if code in ["return items;", "return items"]:
                    logger.info(f"Optimizer: Pruning empty code node '{step.id}'")
                    continue
            new_steps.append(step)
        return new_steps

    def _constant_folding(self, steps: List[RecipeStep]) -> List[RecipeStep]:
        for step in steps:
            if step.template == "if":
                left = str(step.params.get("left", ""))
                right = str(step.params.get("right", ""))
                op = step.params.get("operator", "equal")
                if "{{" not in left and "{{" not in right and "=" not in left:
                    is_true = False
                    if op == "equal": is_true = (left == right)
                    elif op == "notEqual": is_true = (left != right)
                    if is_true:
                        logger.info(f"Optimizer: IF node '{step.id}' is always TRUE.")
                    else:
                        logger.warning(f"Optimizer: IF node '{step.id}' is always FALSE.")
        return steps

    def _analyze_unused_variables(self, steps: List[RecipeStep]):
        defined_vars = set()
        used_vars = set()
        for step in steps:
            if step.template == "set":
                defined_vars.add(step.params.get("name"))
            elif step.template == "set_multi":
                for item in step.params.get("items", []):
                    defined_vars.add(item.get("name"))
        
        regex = re.compile(r'\$json\.([a-zA-Z0-9_]+)|\$json\[["\']([a-zA-Z0-9_]+)["\']\]')
        for step in steps:
            for val in step.params.values():
                val_str = str(val)
                matches = regex.findall(val_str)
                for m in matches:
                    var = m[0] or m[1]
                    if var:
                        used_vars.add(var)
        
        unused = defined_vars - used_vars
        if unused:
            logger.warning(f"Optimizer: Unused variables detected: {unused}")

    def _audit_descriptions(self, steps: List[RecipeStep], strict: bool = False):
        for step in steps:
            if not step.description and not step.notes:
                msg = f"Audit: Step '{step.id}' lacks description or notes."
                # strict checking for docs? usually strict is for correctness.
                # Let's just warn or info.
                # If recipe.strict is True, maybe we enforce docs?
                if strict:
                    logger.warning(msg) # Don't fail build, just warn loudly
                # logger.info(msg) # Too noisy for default