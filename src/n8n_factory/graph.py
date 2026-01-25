from typing import Dict, List, Set, Any
from .logger import logger

class DependencyGraph:
    def __init__(self, steps: List[Any]):
        self.steps = {s.id: s for s in steps}
        self.adj = {s.id: [] for s in steps}
        self.rev_adj = {s.id: [] for s in steps}
        self._build_graph(steps)

    def _build_graph(self, steps):
        previous_id = None
        for i, step in enumerate(steps):
            current_id = step.id
            if step.connections_from is not None:
                for conn in step.connections_from:
                    # Handle str vs Connection object
                    source_id = conn if isinstance(conn, str) else conn.node
                    
                    if source_id in self.steps:
                        self.adj[source_id].append(current_id)
                        self.rev_adj[current_id].append(source_id)
            elif previous_id:
                self.adj[previous_id].append(current_id)
                self.rev_adj[current_id].append(previous_id)
            previous_id = current_id

    def detect_cycles(self):
        visited = set()
        stack = set()
        def visit(node_id):
            if node_id in stack:
                raise ValueError(f"Cycle detected involving step '{node_id}'")
            if node_id in visited:
                return
            stack.add(node_id)
            visited.add(node_id)
            for neighbor in self.adj.get(node_id, []):
                visit(neighbor)
            stack.remove(node_id)
        for node_id in self.steps:
            visit(node_id)

    def detect_orphans(self, strict: bool = False):
        for step in self.steps.values():
            tmpl = step.template.lower()
            is_trigger = any(x in tmpl for x in ["trigger", "webhook", "schedule", "start", "kafka", "telegram", "discord"])
            is_first = (step == list(self.steps.values())[0])
            
            if not is_trigger and not self.rev_adj[step.id]:
                if not is_first:
                    msg = f"Orphan Step Detected: '{step.id}' (template: {step.template}) has no incoming connections."
                    if strict:
                        raise ValueError(msg)
                    logger.warning(msg)

    def get_downstream_nodes(self, node_id: str) -> Set[str]:
        reachable = set()
        queue = [node_id]
        while queue:
            curr = queue.pop(0)
            if curr in reachable: continue
            reachable.add(curr)
            queue.extend(self.adj.get(curr, []))
        return reachable

    def to_mermaid(self) -> str:
        lines = ["graph TD;"]
        for step_id, targets in self.adj.items():
            step = self.steps[step_id]
            if "webhook" in step.template:
                lines.append(f"    {step_id}([{step_id}]);")
            else:
                lines.append(f"    {step_id}[{step_id}]")
            
            for target in targets:
                lines.append(f"    {step_id} --> {target}")
        return "\n".join(lines)