import pytest
import sys
import os
import yaml
import json
import logging
from unittest.mock import patch
from n8n_factory.cli import main

def test_cli_build(temp_templates_dir, tmp_path, capsys):
    recipe_path = tmp_path / "recipe.yaml"
    recipe_data = {
        "name": "CLI Test",
        "steps": [{"id": "s1", "template": "webhook", "params": {"path": "p", "method": "m"}}]
    }
    with open(recipe_path, "w") as f:
        yaml.dump(recipe_data, f)
        
    output_path = tmp_path / "output.json"
    
    with patch.object(sys, 'argv', ["n8n-factory", "build", str(recipe_path), "-o", str(output_path), "-t", temp_templates_dir]):
        main()
        
    assert output_path.exists()
    with open(output_path) as f:
        data = json.load(f)
        assert data["name"] == "CLI Test"
    
    captured = capsys.readouterr()
    assert "Successfully built workflow" in captured.out

def test_cli_simulate(temp_templates_dir, tmp_path, caplog):
    caplog.set_level(logging.INFO)
    recipe_path = tmp_path / "recipe.yaml"
    recipe_data = {
        "name": "Sim Test",
        "steps": [{"id": "s1", "template": "webhook", "params": {"path": "p", "method": "m"}}]
    }
    with open(recipe_path, "w") as f:
        yaml.dump(recipe_data, f)
        
    with patch.object(sys, 'argv', ["n8n-factory", "simulate", str(recipe_path)]):
        main()
    
    assert "--- Starting Simulation: Sim Test ---" in caplog.text

def test_cli_optimize(temp_templates_dir, tmp_path, capsys):
    recipe_path = tmp_path / "recipe.yaml"
    recipe_data = {
        "name": "Opt Test",
        "steps": [
            {"id": "s1", "template": "set", "params": {"name": "a", "value": "1"}},
            {"id": "s2", "template": "set", "params": {"name": "b", "value": "2"}}
        ]
    }
    with open(recipe_path, "w") as f:
        yaml.dump(recipe_data, f)
    
    output_path = tmp_path / "optimized.yaml"
    
    with patch.object(sys, 'argv', ["n8n-factory", "optimize", str(recipe_path), "-o", str(output_path)]):
        main()
        
    assert output_path.exists()
    with open(output_path) as f:
        data = yaml.safe_load(f)
        assert len(data["steps"]) == 1
        assert data["steps"][0]["template"] == "set_multi"
        
    captured = capsys.readouterr()
    assert "Optimized recipe saved" in captured.out

def test_cli_load_recipe_errors(tmp_path, caplog):
    caplog.set_level(logging.ERROR)
    # Test file not found
    with pytest.raises(SystemExit):
        with patch.object(sys, 'argv', ["n8n-factory", "build", "non_existent.yaml"]):
            main()
    assert "Recipe file not found" in caplog.text

    # Test invalid YAML
    bad_yaml = tmp_path / "bad.yaml"
    with open(bad_yaml, "w") as f:
        f.write("{ invalid yaml")
    
    with pytest.raises(SystemExit):
        with patch.object(sys, 'argv', ["n8n-factory", "build", str(bad_yaml)]):
            main()
    assert "Error parsing YAML" in caplog.text

def test_cli_no_command(capsys):
    with patch.object(sys, 'argv', ["n8n-factory"]):
        main()
    captured = capsys.readouterr()
    assert "usage: n8n-factory" in captured.out