import pytest
import json
import os
import yaml
from unittest.mock import MagicMock, patch, mock_open
from n8n_factory.commands.policy import policy_check_command
from n8n_factory.commands.template_extract import template_extract_command
from n8n_factory.commands.config import config_command
from n8n_factory.models import Recipe, RecipeStep

# --- Policy Tests ---
def test_policy_skip(capsys):
    with patch("os.path.exists", return_value=False):
        policy_check_command(Recipe(name="R", steps=[]), json_output=True)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "skipped"

def test_policy_violations(tmp_path, capsys):
    policy_file = tmp_path / "policy.yaml"
    with open(policy_file, "w") as f:
        yaml.dump({
            "forbidden_nodes": ["forbidden"],
            "naming_convention": "^step_.*",
            "required_settings": {"retryOnFail": True}
        }, f)
    
    recipe = Recipe(name="R", steps=[
        RecipeStep(id="bad_id", template="forbidden"),
        RecipeStep(id="step_1", template="http_request", retry=None) # missing retry
    ])
    
    with patch("os.path.exists", return_value=True): # Mock exists for policy_path
        # but mock_open needs to handle the file read.
        # Since tmp_path file exists physically, we don't need mock_open if we pass path.
        pass
    
    # We pass explicit path
    policy_check_command(recipe, policy_path=str(policy_file), json_output=True)
    
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["passed"] is False
    assert len(data["violations"]) >= 3
    msg = str(data["violations"])
    assert "forbidden template" in msg
    assert "naming convention" in msg
    assert "retry configuration" in msg

def test_policy_pass(tmp_path, capsys):
    policy_file = tmp_path / "policy.yaml"
    with open(policy_file, "w") as f:
        yaml.dump({"allowed_nodes": ["good"]}, f)
    
    recipe = Recipe(name="R", steps=[RecipeStep(id="s1", template="good")])
    
    policy_check_command(recipe, policy_path=str(policy_file), json_output=True)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["passed"] is True

# --- Template Extract Tests ---
def test_extract_not_found(capsys):
    template_extract_command("missing.json", "node", json_output=True)
    captured = capsys.readouterr()
    assert "error" in captured.out

def test_extract_node_missing(tmp_path, capsys):
    wf = tmp_path / "wf.json"
    with open(wf, "w") as f:
        json.dump({"nodes": []}, f)
        
    template_extract_command(str(wf), "node", json_output=True)
    captured = capsys.readouterr()
    assert "not found in workflow" in captured.out

def test_extract_success(tmp_path, capsys):
    wf = tmp_path / "wf.json"
    with open(wf, "w") as f:
        json.dump({
            "nodes": [{
                "name": "target",
                "type": "t",
                "parameters": {"key": "val", "long": "x"*200}
            }]
        }, f)
        
    out_dir = tmp_path / "tmpl"
    template_extract_command(str(wf), "target", output_dir=str(out_dir), json_output=True)
    
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "extracted"
    
    out_file = out_dir / "target.json"
    assert out_file.exists()
    with open(out_file) as f:
        tmpl = json.load(f)
        assert "{{ key | default('val') }}" in tmpl["parameters"]["key"]
        assert tmpl["parameters"]["long"] == "x"*200 # long string not parameterized

# --- Config Tests ---
def test_config_defaults(capsys):
    with patch("os.path.exists", return_value=False):
        config_command(json_output=True)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["n8n_url"] == "http://localhost:5678"

def test_config_file(tmp_path, capsys):
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        with open(".n8n-factory.yaml", "w") as f:
            yaml.dump({"n8n_url": "custom"}, f)
            
        config_command(json_output=True)
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["n8n_url"] == "custom"
        assert data["templates_dir"] == "templates" # default preserved
    finally:
        os.chdir(original_cwd)

def test_config_error(capsys):
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", side_effect=Exception("Read fail")):
            config_command(json_output=True)
    captured = capsys.readouterr()
    assert "error" in captured.out
