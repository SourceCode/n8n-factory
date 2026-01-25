from typing import Dict, Any, List, Set, Union
import datetime
import re
import sys
try:
    from importlib.metadata import version
except ImportError:
    version = None

from .models import Recipe, Connection
from .loader import TemplateLoader
from .logger import logger
from .layout import AutoLayout
from .graph import DependencyGraph

class WorkflowAssembler:
    def __init__(self, templates_dir: Union[str, List[str]] = "templates"):
        self.loader = TemplateLoader(templates_dir)
        self.layout_engine = AutoLayout()

    def assemble(self, recipe: Recipe) -> Dict[str, Any]:
        # Improvement #3: Version Pinning
        if recipe.n8n_factory_version and version:
            try:
                current_ver = version("n8n_factory")
                # Simple string compare for now or assume user uses loose semver
                if current_ver < recipe.n8n_factory_version:
                    logger.warning(f"Warning: Recipe requires n8n-factory >= {recipe.n8n_factory_version}, current is {current_ver}")
            except:
                pass

        self._scan_for_secrets(recipe)
        
        graph = DependencyGraph(recipe.steps)
        graph.detect_cycles()
        graph.detect_orphans(strict=recipe.strict)

        nodes = []
        connections = {}
        id_to_name = {}
        
        seen_names = set()
        for step in recipe.steps:
            if step.id.lower() in seen_names:
                msg = f"Duplicate Node ID (case-insensitive): '{step.id}'"
                if recipe.strict:
                    raise ValueError(msg)
                logger.warning(msg)
            seen_names.add(step.id.lower())
            id_to_name[step.id] = step.id
            
        previous_node_name = None

        for i, step in enumerate(recipe.steps):
            try:
                node_config = self.loader.render_template(step.template, step.params, global_context=recipe.globals)
            except ValueError as e:
                raise e

            node_name = step.id
            node_config["name"] = node_name
            
            if step.position:
                node_config["position"] = step.position
            else:
                node_config["position"] = [0, 0]

            if step.notes:
                node_config["notesInFlow"] = True
                node_config["notes"] = step.notes
                
            if step.disabled:
                node_config["disabled"] = True
                
            if step.retry:
                node_config["retryOnFail"] = True
                node_config["maxTries"] = step.retry.maxTries
                node_config["waitBetweenTries"] = step.retry.waitBetweenTries
                
            if step.color:
                if "parameters" not in node_config:
                    node_config["parameters"] = {}
                node_config["parameters"]["color"] = step.color

            nodes.append(node_config)
            
            # Connection Logic
            if step.connections_from is not None:
                for conn in step.connections_from:
                    # Handle str vs Connection
                    if isinstance(conn, str):
                        source_id = conn
                        conn_type = "main"
                        conn_index = 0
                    else:
                        source_id = conn.node
                        conn_type = conn.type
                        conn_index = conn.index

                    source_name = id_to_name.get(source_id)
                    if not source_name:
                         raise ValueError(f"Step '{step.id}' references unknown step '{source_id}'")
                    
                    self._add_connection(connections, source_name, node_name, conn_type, conn_index)
            elif previous_node_name:
                self._add_connection(connections, previous_node_name, node_name)

            if step.debug:
                debug_node_name = f"debug_{step.id}"
                debug_config = self.loader.render_template("debug_logger", {"source_step": step.id})
                debug_config["name"] = debug_node_name
                node_config["position"] = [0,0]
                nodes.append(debug_config)
                
                self._add_connection(connections, node_name, debug_node_name)
                previous_node_name = debug_node_name
            else:
                previous_node_name = node_name

        self.layout_engine.layout(nodes, connections)

        workflow = {
            "name": recipe.name,
            "nodes": nodes,
            "connections": connections,
            "meta": {
                "instanceId": "generated_by_n8n_factory",
                "generatedAt": datetime.datetime.now().isoformat(),
                "description": recipe.description or "",
                "tags": recipe.tags,
                "version": "1.6.0" 
            }
        }
        
        # Improvement #2: Workflow Meta
        if recipe.meta:
            workflow["meta"].update(recipe.meta)
        
        return workflow

    def _add_connection(self, connections: Dict, source: str, target: str, type: str = "main", index: int = 0):
        if source not in connections:
            connections[source] = {}
        
        if type not in connections[source]:
            connections[source][type] = []
            
        # Ensure list has enough indices
        while len(connections[source][type]) <= index:
            connections[source][type].append([])
            
        connections[source][type][index].append({
            "node": target,
            "type": "main", # Target input is usually 'main' unless specified otherwise (not supported in connections_from yet)
            "index": 0
        })

    def _scan_for_secrets(self, recipe: Recipe):
        patterns = [
            (r'(api_?key|token|secret|password|passwd)', "Potential Secret Key"),
            (r'sk-[a-zA-Z0-9]{20,}', "OpenAI/Stripe Key format")
        ]
        
        for step in recipe.steps:
            for k, v in step.params.items():
                val_str = str(v)
                for pat, desc in patterns:
                    if re.search(pat, k, re.IGNORECASE) or re.search(pat, val_str, re.IGNORECASE):
                        if "${" in val_str: 
                            continue
                        msg = f"Security Warning: Step '{step.id}' param '{k}' matches {desc} pattern."
                        logger.warning(msg)
                        if recipe.strict:
                            raise ValueError(msg)
