import os
import yaml
import sys
from typing import List, Dict, Optional, Set, Union
from .models import Recipe, ImportItem, Connection
from .logger import logger

def load_recipe(path: str, env_name: Optional[str] = None) -> Recipe:
    return _load_recipe_recursive(path, env_name, visited=set())

def _load_recipe_recursive(path: str, env_name: Optional[str], visited: Set[str]) -> Recipe:
    abs_path = os.path.abspath(path)
    if abs_path in visited:
        raise ValueError(f"Circular import detected: {path}")
    
    visited.add(abs_path)
    
    if not os.path.exists(path):
        logger.error(f"Recipe file not found: {path}")
        sys.exit(1)
        
    base_dir = os.path.dirname(abs_path)
    
    with open(path, 'r', encoding='utf-8') as f:
        try:
            data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML {path}: {e}")
            sys.exit(1)

    if env_name:
        config_path = os.path.join("config", f"{env_name}.yaml")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as cf:
                    env_config = yaml.safe_load(cf)
                    if env_config:
                        data.setdefault("globals", {}).update(env_config)
            except Exception:
                pass

    final_steps = []
    imports = data.get("imports", [])
    for item in imports:
        import_path = None
        namespace = None
        
        if isinstance(item, str):
            import_path = item
        elif isinstance(item, dict):
            import_path = item.get("path")
            namespace = item.get("namespace")
            
        if not import_path:
            continue
            
        full_import_path = os.path.join(base_dir, import_path)
        
        try:
            imported_recipe = _load_recipe_recursive(full_import_path, env_name=None, visited=visited)
            
            prefix = namespace if namespace else os.path.splitext(os.path.basename(import_path))[0]
            
            for step in imported_recipe.steps:
                orig_id = step.id
                step.id = f"{prefix}_{orig_id}"
                
                if step.connections_from:
                    new_conns = []
                    for c in step.connections_from:
                        if isinstance(c, str):
                            new_conns.append(f"{prefix}_{c}")
                        elif isinstance(c, Connection): # Pydantic object
                            c.node = f"{prefix}_{c.node}"
                            new_conns.append(c)
                        elif isinstance(c, dict): # If parsed as dict before model validation?
                            # Should be objects if imported_recipe is Recipe.
                            # But wait, imported_recipe is Recipe object.
                            # So c is Connection or str.
                            pass
                    step.connections_from = new_conns
                
                final_steps.append(step)
                
        except ValueError as e:
            raise e
        except Exception as e:
            logger.error(f"Failed to import {full_import_path}: {e}")
            sys.exit(1)

    raw_steps = data.get("steps", [])
    imported_dicts = [s.model_dump(exclude_none=True) for s in final_steps]
    combined_steps = imported_dicts + raw_steps
    
    data["steps"] = combined_steps
    
    try:
        return Recipe(**data)
    except Exception as e:
        logger.error(f"Error validating Recipe {path}: {e}")
        sys.exit(1)