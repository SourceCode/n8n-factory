import pytest
import json
import os
from unittest.mock import MagicMock, patch, mock_open
from n8n_factory.commands.security import security_command
from n8n_factory.commands.visualize import visualize_recipe
from n8n_factory.commands.mock import mock_generate_command
from n8n_factory.hardener import WorkflowHardener
from n8n_factory.models import Recipe, RecipeStep, Connection

# --- Security Tests ---
@pytest.fixture
def mock_recipe_security_issues():
    steps = [
        RecipeStep(id="s1", template="webhook", params={"api_key": "12345"}), # Key name match
        RecipeStep(id="s2", template="set", params={"value": "sk-12345678901234567890"}) # Value match
    ]
    return Recipe(name="SecTest", steps=steps)

@patch("n8n_factory.commands.security.console")
def test_security_issues(mock_console, mock_recipe_security_issues):
    security_command(mock_recipe_security_issues)
    assert mock_console.print.call_count >= 1
    # We expect "Security Issues Found"

def test_security_json(mock_recipe_security_issues, capsys):
    security_command(mock_recipe_security_issues, json_output=True)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "failed"
    assert len(data["issues"]) == 2

def test_security_clean(capsys):
    recipe = Recipe(name="Clean", steps=[RecipeStep(id="s1", template="code", params={"p": "${env.VAR}"})])
    security_command(recipe, json_output=True)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "passed"

# --- Visualize Tests ---
@pytest.fixture
def mock_recipe_graph():
    steps = [
        RecipeStep(id="s1", template="webhook", params={}),
        RecipeStep(id="s2", template="set", params={"val": "={{ $node['s1'].json.id }}"}, connections_from=["s1"]),
        RecipeStep(id="s3", template="code", params={}, connections_from=[Connection(node="s2", type="main")])
    ]
    return Recipe(name="GraphTest", steps=steps)

@patch("n8n_factory.commands.visualize.console")
def test_visualize_mermaid(mock_console, mock_recipe_graph, capsys):
    visualize_recipe(mock_recipe_graph, format="mermaid")
    captured = capsys.readouterr()
    assert "graph TD;" in captured.out
    assert "s1 --> s2;" in captured.out
    assert "s2 --> s3;" in captured.out

def test_visualize_json(mock_recipe_graph, capsys):
    visualize_recipe(mock_recipe_graph, format="json")
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert len(data["nodes"]) == 3
    # check expression edge
    # Regex was fixed in visualize.py to support ['...']
    expr_edge = next((e for e in data["edges"] if e["type"] == "expression"), None)
    assert expr_edge is not None
    assert expr_edge["source"] == "s1"
    assert expr_edge["target"] == "s2"
def test_visualize_dot(mock_recipe_graph, capsys):
    visualize_recipe(mock_recipe_graph, format="dot")
    captured = capsys.readouterr()
    assert "digraph G {" in captured.out
    assert '"s1" -> "s2";' in captured.out

@patch("n8n_factory.commands.visualize.console")
def test_visualize_ascii(mock_console, mock_recipe_graph):
    visualize_recipe(mock_recipe_graph, format="ascii")
    assert mock_console.print.call_count >= 1

# --- Mock Tests ---
@patch("n8n_factory.commands.mock.load_recipe")
def test_mock_command_webhook(mock_load, tmp_path, capsys):
    recipe = Recipe(name="M", steps=[RecipeStep(id="s1", template="webhook")])
    mock_load.return_value = recipe
    out = tmp_path / "mock.json"
    
    mock_generate_command("r.yaml", output_file=str(out), json_output=True)
    
    assert out.exists()
    with open(out) as f:
        data = json.load(f)
        assert "body" in data[0]

@patch("n8n_factory.commands.mock.load_recipe")
def test_mock_command_schedule(mock_load, tmp_path):
    recipe = Recipe(name="M", steps=[RecipeStep(id="s1", template="schedule")])
    mock_load.return_value = recipe
    out = tmp_path / "mock.json"
    
    mock_generate_command("r.yaml", output_file=str(out))
    
    with open(out) as f:
        data = json.load(f)
        assert "timestamp" in data[0]

@patch("n8n_factory.commands.mock.load_recipe")
def test_mock_empty(mock_load, capsys):
    recipe = Recipe(name="M", steps=[])
    mock_load.return_value = recipe
    mock_generate_command("r.yaml", json_output=True)
    captured = capsys.readouterr()
    assert "error" in captured.out

# --- Hardener Tests ---
def test_harden_json_logging():
    hardener = WorkflowHardener()
    wf = {
        "nodes": [
            {"name": "Start", "type": "n8n-nodes-base.start", "typeVersion": 1, "position": [100, 100]}
        ],
        "connections": {
            "Start": {"main": [[{"node": "Next", "type": "main", "index": 0}]]}
        }
    }
    
    hardened = hardener.harden_json(wf, add_logging=True)
    
    nodes = hardened["nodes"]
    assert any(n["name"].startswith("Logger_Start") for n in nodes)
    
    # Check connections re-wiring
    # Start -> Logger
    assert hardened["connections"]["Start"]["main"][0][0]["node"].startswith("Logger_Start")
    # Logger -> Next
    logger_name = next(n["name"] for n in nodes if n["name"].startswith("Logger_Start"))
    assert hardened["connections"][logger_name]["main"][0][0]["node"] == "Next"

def test_harden_json_error():
    hardener = WorkflowHardener()
    wf = {"nodes": []}
    hardened = hardener.harden_json(wf, add_error_trigger=True)
    nodes = hardened["nodes"]
    assert any(n["type"] == "n8n-nodes-base.errorTrigger" for n in nodes)
    assert any(n["name"] == "Error Logger" for n in nodes)

def test_harden_recipe():
    hardener = WorkflowHardener()
    recipe = Recipe(name="R", steps=[RecipeStep(id="s1", template="t", debug=False)])
    hardened = hardener.harden_recipe(recipe, add_logging=True)
    assert hardened.steps[0].debug is True
