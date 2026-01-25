from typing import Dict, List, Any

class AutoLayout:
    def __init__(self, x_spacing=250, y_spacing=150):
        self.x_spacing = x_spacing
        self.y_spacing = y_spacing

    def layout(self, nodes: List[Dict], connections: Dict) -> None:
        """
        Modifies the 'position' attribute of nodes in-place.
        """
        node_names = {n["name"] for n in nodes}
        node_lookup = {n["name"]: n for n in nodes}
        
        children_map = {name: [] for name in node_names}
        parents_map = {name: 0 for name in node_names}

        for source, targets in connections.items():
            if source not in node_names: continue
            for output_list in targets.get("main", []):
                for conn in output_list:
                    target_name = conn["node"]
                    if target_name in node_names:
                        children_map[source].append(target_name)
                        parents_map[target_name] += 1

        # Calculate Rank (Depth)
        ranks = {name: 0 for name in node_names}
        queue = [name for name, count in parents_map.items() if count == 0]
        visited = set()
        
        while queue:
            current = queue.pop(0)
            visited.add(current)
            current_rank = ranks[current]
            
            for child in children_map[current]:
                if ranks[child] < current_rank + 1:
                    ranks[child] = current_rank + 1
                if child not in visited and child not in queue:
                     queue.append(child)

        # Assign positions
        rank_groups = {}
        for name, rank in ranks.items():
            if rank not in rank_groups:
                rank_groups[rank] = []
            rank_groups[rank].append(name)

        # Iterate ranks and assign X, Y
        for rank in sorted(rank_groups.keys()):
            group = rank_groups[rank]
            x = rank * self.x_spacing + 250
            
            # Improvement #11: Center Y around 0
            total_height = (len(group) - 1) * self.y_spacing
            y_start = -total_height / 2
            
            for i, name in enumerate(group):
                y = y_start + (i * self.y_spacing)
                
                node = node_lookup[name]
                # Only update if default [0,0] (which is set by assembler)
                # or if we strictly enforce layout. 
                # Assembler sets [0,0] default if not provided in recipe.
                # If user provided explicit position, it would be non-zero (likely).
                # But strict check: [0,0]
                if node.get("position") == [0, 0]:
                    node["position"] = [x, y]