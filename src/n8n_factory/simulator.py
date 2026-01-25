from typing import Any, Dict, List
import re
import time
import json
import csv
from .models import Recipe
from .logger import logger

class WorkflowSimulator:
    def __init__(self):
        self.history: List[Dict[str, Any]] = []

    def _resolve_expressions(self, value: Any, context_item: Dict) -> Any:
        if isinstance(value, str):
            # Matches {{ $json.key }} with optional spaces
            pattern = re.compile(r'{{\s*[$]json\.([a-zA-Z0-9_]+)\s*}}')
            def replace_match(match):
                field = match.group(1)
                data = context_item.get("json", {})
                val = data.get(field, None)
                return str(val) if val is not None else match.group(0)
            return pattern.sub(replace_match, value)
        elif isinstance(value, dict):
             return {k: self._resolve_expressions(v, context_item) for k, v in value.items()}
        elif isinstance(value, list):
             return [self._resolve_expressions(v, context_item) for v in value]
        return value

    def simulate(self, recipe: Recipe, max_steps: int = 100, interactive: bool = False, step_mode: bool = False) -> List[Dict[str, Any]]:
        self.history = []
        logger.info(f"--- Starting Simulation: {recipe.name} ---")
        
        current_items = [{"json": {}}] 
        
        for i, step in enumerate(recipe.steps):
            if i >= max_steps:
                 logger.warning("Simulation limit reached. Stopping.")
                 break

            if step_mode:
                input(f"Step {i+1}: {step.id}. Press Enter to execute...")

            if step.breakpoint and interactive:
                print(f"\n[BREAKPOINT] Step: {step.id}")
                print(f"Current Input: {json.dumps(current_items, indent=2)}")
                input("Press Enter to continue...")

            logger.info(f"[Step {i+1}: {step.id} ({step.template})]")
            
            if step.mock_latency:
                logger.info(f"  > Simulating latency: {step.mock_latency}ms")

            if step.mock_error:
                logger.error(f"  > Simulated Error: {step.mock_error}")
                self.history.append({
                    "step_id": step.id,
                    "template": step.template,
                    "input": current_items,
                    "error": step.mock_error
                })
                break

            step_result = {
                "step_id": step.id,
                "template": step.template,
                "input": current_items
            }
            
            if step.mock:
                logger.info("  > Using Mock Data.")
                mock_data = step.mock
                if isinstance(mock_data, str) and mock_data.startswith("file:"):
                    import os
                    path = mock_data[5:]
                    if os.path.exists(path):
                        with open(path, 'r') as f:
                            mock_data = json.load(f)
                    else:
                        logger.warning(f"Mock data file not found: {path}")

                if isinstance(mock_data, list):
                    current_items = mock_data
                elif isinstance(mock_data, dict):
                    if "json" in mock_data:
                        current_items = [mock_data]
                    else:
                        current_items = [{"json": mock_data}]
                else:
                    current_items = [{"json": {"value": mock_data}}]
            else:
                if step.template == "if":
                    logger.info("  > Evaluating IF condition...")
                    left_raw = step.params.get("left")
                    right_raw = step.params.get("right")
                    op = step.params.get("operator", "equal")
                    
                    ctx = current_items[0] if current_items else {"json": {}}
                    left = self._resolve_expressions(left_raw, ctx)
                    right = self._resolve_expressions(right_raw, ctx)
                    
                    is_true = False
                    if op == "equal":
                        is_true = (str(left) == str(right))
                    elif op == "notEqual":
                        is_true = (str(left) != str(right))
                    
                    logger.info(f"    Condition: '{left}' {op} '{right}' -> {is_true}")
                
                logger.info("  > Passing previous output.")
            
            step_result["output"] = current_items
            self.history.append(step_result)
            
            preview = str(current_items)
            if len(preview) > 100:
                preview = preview[:100] + "..."
            logger.info(f"  Output: {preview}")
            
        logger.info("\n--- Simulation Complete ---")
        
        if recipe.assertions:
            self._evaluate_assertions(recipe.assertions, self.history)
            
        return self.history

    def _evaluate_assertions(self, assertions: List[str], history: List[Dict]):
        logger.info("Running Assertions...")
        final_output = history[-1]['output'] if history and 'output' in history[-1] else []
        context = {
            "history": history,
            "output": final_output,
            "json": final_output[0].get("json") if final_output else {}
        }
        for expr in assertions:
            try:
                result = eval(expr, {"__builtins__": None}, context)
                if result:
                    logger.info(f"  [PASS] {expr}")
                else:
                    logger.error(f"  [FAIL] {expr}")
            except Exception as e:
                logger.error(f"  [ERROR] {expr}: {e}")

    def generate_html_report(self, history: List[Dict], output_path: str):
        html = """
        <html>
        <head>
            <title>Simulation Report</title>
            <style>
                body { font-family: sans-serif; padding: 20px; }
                .step { border: 1px solid #ccc; margin-bottom: 20px; padding: 10px; border-radius: 5px; }
                .step.error { border-color: red; background-color: #fff0f0; }
                .step h3 { margin-top: 0; background: #f0f0f0; padding: 5px; }
                pre { background: #333; color: #fff; padding: 10px; overflow-x: auto; }
            </style>
        </head>
        <body>
            <h1>Simulation Report</h1>
        """
        for item in history:
            is_error = "error" in item
            cls = "step error" if is_error else "step"
            html += f"""
            <div class="{cls}">
                <h3>{item['step_id']} <small>({item['template']})</small></h3>
                <p><strong>Input:</strong></p>
                <pre>{json.dumps(item.get('input'), indent=2)}</pre>
            """
            if is_error:
                 html += f"<p><strong>Error:</strong> {item['error']}</p>"
            else:
                 html += f"<p><strong>Output:</strong></p><pre>{json.dumps(item.get('output'), indent=2)}</pre>"
            html += "</div>"
        html += "</body></html>"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

    def export_csv(self, history: List[Dict], output_path: str):
        rows = []
        for item in history:
            row = {
                "step_id": item["step_id"],
                "template": item["template"],
                "input": json.dumps(item.get("input")),
                "output": json.dumps(item.get("output")),
                "error": item.get("error", "")
            }
            rows.append(row)
            
        if rows:
            with open(output_path, "w", newline='', encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)