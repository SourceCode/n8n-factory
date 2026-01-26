import pytest
import os
import json
import yaml
from unittest.mock import MagicMock, patch, mock_open
from n8n_factory.commands.audit import audit_command
from n8n_factory.commands.cost import cost_command
from n8n_factory.commands.creds import creds_command
from n8n_factory.commands.import_workflow import import_command
from n8n_factory.models import Recipe, RecipeStep

# --- Audit Tests ---
@pytest.fixture
def mock_recipe_issues():
    steps = [
        RecipeStep(id="s1", template="webhook", params={"authentication": "none"}),
        RecipeStep(id="s2", template="http_request", params={}),
        RecipeStep(id="s3", template="code", params={})
    ]
    return Recipe(name="AuditTest", steps=steps)

@pytest.fixture
def mock_recipe_clean():
    steps = [
        RecipeStep(id="s1", template="webhook", params={"authentication": "basic"}),
        RecipeStep(id="s2", template="http_request", params={"timeout": 10})
    ]
    return Recipe(name="CleanTest", steps=steps)

@patch("n8n_factory.commands.audit.load_recipe")
@patch("n8n_factory.commands.audit.console")
def test_audit_issues(mock_console, mock_load, mock_recipe_issues):
    mock_load.return_value = mock_recipe_issues
    audit_command("test.yaml")
    assert mock_console.print.call_count >= 1
    # Check for specific strings if possible, but call_count proves execution path

@patch("n8n_factory.commands.audit.load_recipe")
def test_audit_json(mock_load, mock_recipe_issues, capsys):
    mock_load.return_value = mock_recipe_issues
    audit_command("test.yaml", json_output=True)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert len(data["issues"]) == 2
    msgs = [i["msg"] for i in data["issues"]]
    assert "HTTP node missing explicit timeout config" in msgs
    assert "Webhook has no authentication configured" in msgs
    
@patch("n8n_factory.commands.audit.load_recipe")
@patch("n8n_factory.commands.audit.console")
def test_audit_clean(mock_console, mock_load, mock_recipe_clean):
    mock_load.return_value = mock_recipe_clean
    audit_command("test.yaml")
    mock_console.print.assert_called_with("[bold green]Audit Passed.[/bold green]")

# --- Cost Tests ---
@pytest.fixture
def mock_recipe_cost():
    steps = [
        RecipeStep(id="s1", template="openai", params={}),
        RecipeStep(id="s2", template="split", params={}),
        RecipeStep(id="s3", template="code", params={})
    ]
    return Recipe(name="CostTest", steps=steps)

@patch("n8n_factory.commands.cost.load_recipe")
@patch("n8n_factory.commands.cost.console")
def test_cost_command(mock_console, mock_load, mock_recipe_cost):
    mock_load.return_value = mock_recipe_cost
    cost_command("test.yaml")
    mock_console.print.call_count >= 1

@patch("n8n_factory.commands.cost.load_recipe")
def test_cost_json(mock_load, mock_recipe_cost, capsys):
    mock_load.return_value = mock_recipe_cost
    cost_command("test.yaml", json_output=True)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["nodes"] == 3
    assert data["estimated_execution_units"] == 3 + (1 * 9) # 12

# --- Creds Tests ---
def test_creds_scaffold(tmp_path, capsys):
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        creds_command(scaffold=True, json_output=True)
        assert os.path.exists(".env.example")
        
        # Test existing
        creds_command(scaffold=True, json_output=True)
    finally:
        os.chdir(original_cwd)

def test_creds_check(capsys):
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-...", "POSTGRES_USER": "u"}, clear=True):
        creds_command(json_output=True)
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["openai"] == "Available"
        assert data["postgres"] == "Partial"
        assert data["aws"] == "Missing"

# --- Import Tests ---
def test_import_success(tmp_path, capsys):
    infile = tmp_path / "in.json"
    with open(infile, "w") as f:
        json.dump({
            "name": "Imp", 
            "nodes": [{"name": "n1", "type": "n8n-nodes-base.set", "typeVersion": 1, "parameters": {}}],
            "connections": {"n1": {"main": [[{"node": "n2"}]]}} # n2 doesn't exist but logic should process
        }, f)
    
    outfile = tmp_path / "out.yaml"
    import_command(str(infile), str(outfile), json_output=True)
    
    assert outfile.exists()
    captured = capsys.readouterr()
    assert "imported" in captured.out

def test_import_file_not_found(capsys):
    import_command("missing.json", json_output=True)
    captured = capsys.readouterr()
    assert "Failed to load" in captured.out

def test_import_save_error(tmp_path, capsys):
    infile = tmp_path / "in.json"
    with open(infile, "w") as f:
        json.dump({"name": "Imp"}, f)
        
    # simulate write error by directory
    import_command(str(infile), str(tmp_path), json_output=True) # tmp_path is dir, open(dir, 'w') fails
    captured = capsys.readouterr()
    assert "Failed to save" in captured.out
