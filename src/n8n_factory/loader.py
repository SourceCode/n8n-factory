import json
import os
import re
from typing import Any, Dict, List, Optional, Union
from jinja2 import Environment, FileSystemLoader, StrictUndefined, meta
from dotenv import load_dotenv
from .logger import logger

load_dotenv()

class TemplateLoader:
    def __init__(self, templates_dir: Union[str, List[str]] = "templates"):
        if isinstance(templates_dir, str):
            self.search_paths = [templates_dir]
        else:
            self.search_paths = templates_dir

        self.env = Environment(
            loader=FileSystemLoader(self.search_paths),
            undefined=StrictUndefined
        )
        self.env.globals['read_file'] = self._read_file_helper
        self.env.globals['expr'] = self._expr_helper
        
        self._template_cache = {}

    def _read_file_helper(self, path: str) -> str:
        if not os.path.exists(path):
             raise FileNotFoundError(f"File helper could not find: {path}")
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def _expr_helper(self, path: str) -> str:
        return f"{{{{ ${path} }}}}"

    def load_template_raw(self, template_name: str) -> str:
        if template_name in self._template_cache:
            return self._template_cache[template_name]

        found_path = None
        for base_dir in self.search_paths:
            path = os.path.join(base_dir, f"{template_name}.json")
            if os.path.exists(path):
                found_path = path
                break
        
        if not found_path:
            raise FileNotFoundError(f"Template not found: {template_name} in {self.search_paths}")
            
        with open(found_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self._template_cache[template_name] = content
            return content

    def _resolve_env_vars(self, value: Any) -> Any:
        if isinstance(value, str):
            pattern = re.compile(r'\$\{?([a-zA-Z0-9_]+)\}?')
            def replace_match(match):
                var_name = match.group(1)
                val = os.getenv(var_name)
                if val is None:
                    return match.group(0)
                return val
            return pattern.sub(replace_match, value)
        elif isinstance(value, dict):
            return {k: self._resolve_env_vars(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._resolve_env_vars(v) for v in value]
        return value

    def render_template(self, template_name: str, params: Dict[str, Any], global_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        context = {}
        if global_context:
            context.update(global_context)
        context.update(params)
        resolved_context = self._resolve_env_vars(context)
        
        raw_content = self.load_template_raw(template_name)
        
        try:
            template = self.env.get_template(f"{template_name}.json")
            rendered_content = template.render(**resolved_context)
        except Exception as e:
             raise ValueError(f"Template rendering failed for '{template_name}': {e}")
        
        try:
            data = json.loads(rendered_content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse rendered JSON for template '{template_name}': {e}")

        data = self._resolve_env_vars(data)
        
        if "_meta" in data and "extends" in data["_meta"]:
            base_name = data["_meta"]["extends"]
            base_data = self.render_template(base_name, params, global_context)
            self._deep_merge(base_data, data)
            data = base_data
            
        if "_meta" in data:
            meta_info = data.pop("_meta")
            self._validate_meta(template_name, meta_info, resolved_context)
            
        return data

    def _deep_merge(self, base: Dict, override: Dict):
        for k, v in override.items():
            if isinstance(v, dict) and k in base and isinstance(base[k], dict):
                self._deep_merge(base[k], v)
            else:
                base[k] = v

    def _validate_meta(self, template_name: str, meta_info: Dict, params: Dict):
        if meta_info.get("deprecated", False):
            logger.warning(f"[DEPRECATED] Template '{template_name}' is deprecated.")

        required = meta_info.get("required_params", [])
        for req in required:
            if req not in params:
                 raise ValueError(f"Template '{template_name}' requires parameter: '{req}'")
        
        param_types = meta_info.get("param_types", {})
        for param, expected_type in param_types.items():
            if param in params:
                val = params[param]
                if expected_type == "number" and not isinstance(val, (int, float)):
                     logger.warning(f"Type Mismatch in '{template_name}': '{param}' expected number, got {type(val)}")
                elif expected_type == "boolean" and not isinstance(val, bool):
                     logger.warning(f"Type Mismatch in '{template_name}': '{param}' expected boolean, got {type(val)}")
