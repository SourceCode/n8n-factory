import pytest
import sys
import yaml
import json
from unittest.mock import patch
from n8n_factory.cli import main

def test_e2e_flow(tmp_path, temp_templates_dir):
    # 1. Create a Recipe
    recipe_path = tmp_path / "e2e_recipe.yaml"
    recipe_data = {
        "name": "E2E Test",
        "steps": [
            {"id": "start", "template": "webhook", "params": {"path": "e2e", "method": "GET"}},
            {"id": "process", "template": "set", "params": {"name": "foo", "value": "bar"}}
        ]
    }
    with open(recipe_path, "w") as f:
        yaml.dump(recipe_data, f)
        
    # 2. Build
    output_path = tmp_path / "e2e.json"
    with patch.object(sys, 'argv', ["n8n-factory", "build", str(recipe_path), "-o", str(output_path), "-t", temp_templates_dir]):
        main()
    
    assert output_path.exists()
    
    # 3. Visualize
    with patch.object(sys, 'argv', ["n8n-factory", "visualize", str(recipe_path)]):
        main() # Just ensure it doesn't crash
        
    # 4. Simulate
    sim_export = tmp_path / "sim.json"
    with patch.object(sys, 'argv', ["n8n-factory", "simulate", str(recipe_path), "--export-json", str(sim_export)]):
        main()
        
    assert sim_export.exists()
