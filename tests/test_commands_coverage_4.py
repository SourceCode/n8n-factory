import pytest
import json
import os
from unittest.mock import MagicMock, patch, mock_open
from n8n_factory.cli import main
from n8n_factory.optimizer import WorkflowOptimizer
from n8n_factory.models import Recipe, RecipeStep
import sys

# --- CLI Tests ---
@patch("sys.argv", ["n8n-factory", "version", "--json"])
def test_cli_version(capsys):
    main()
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "version" in data

@patch("sys.argv", ["n8n-factory", "schema"])
def test_cli_schema(capsys):
    main()
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "properties" in data

@patch("n8n_factory.cli.template_new_command")
def test_cli_template_new(mock_cmd):
    with patch("sys.argv", ["n8n-factory", "template", "new", "--name", "t", "--type", "webhook"]):
        main()
    mock_cmd.assert_called()

@patch("n8n_factory.cli.project_init_command")
def test_cli_project_init(mock_cmd):
    with patch("sys.argv", ["n8n-factory", "project", "init"]):
        main()
    mock_cmd.assert_called()

@patch("n8n_factory.cli.telemetry_export_command")
def test_cli_telemetry(mock_cmd):
    with patch("sys.argv", ["n8n-factory", "telemetry", "--export"]):
        main()
    mock_cmd.assert_called()

@patch("n8n_factory.cli.clean_command")
def test_cli_clean(mock_cmd):
    with patch("sys.argv", ["n8n-factory", "clean"]):
        main()
    mock_cmd.assert_called()

@patch("n8n_factory.cli.config_command")
def test_cli_config(mock_cmd):
    with patch("sys.argv", ["n8n-factory", "config"]):
        main()
    mock_cmd.assert_called()

@patch("n8n_factory.cli.tree_command")
@patch("n8n_factory.cli.load_recipe")
def test_cli_tree(mock_load, mock_cmd):
    with patch("sys.argv", ["n8n-factory", "tree", "r.yaml"]):
        main()
    mock_cmd.assert_called()

@patch("n8n_factory.cli.serve_command")
def test_cli_serve(mock_cmd):
    with patch("sys.argv", ["n8n-factory", "serve", "r.yaml"]):
        main()
    mock_cmd.assert_called()

@patch("n8n_factory.cli.bundle_command")
def test_cli_bundle(mock_cmd):
    with patch("sys.argv", ["n8n-factory", "bundle", "r.yaml"]):
        main()
    mock_cmd.assert_called()

@patch("n8n_factory.cli.benchmark_command")
def test_cli_benchmark(mock_cmd):
    with patch("sys.argv", ["n8n-factory", "benchmark"]):
        main()
    mock_cmd.assert_called()

@patch("n8n_factory.cli.examples_command")
def test_cli_examples(mock_cmd):
    with patch("sys.argv", ["n8n-factory", "examples"]):
        main()
    mock_cmd.assert_called()

# --- Optimizer Tests ---
def test_optimizer_refactor_json():
    opt = WorkflowOptimizer()
    wf = {
        "nodes": [
            {"name": "Set1", "type": "n8n-nodes-base.set", "parameters": {"values": {"string": [{"name": "a", "value": "1"}]}}},
            {"name": "Set2", "type": "n8n-nodes-base.set", "parameters": {"values": {"string": [{"name": "b", "value": "2"}]}}}
        ],
        "connections": {} # Empty connections initially
    }
    # Optimizer refactor_json with reinsert_edges=True should rebuild connections
    res = opt.refactor_json(wf, reinsert_edges=True)
    nodes = res["nodes"]
    assert len(nodes) == 2 # Does not merge in JSON mode currently
    
    # Check connections rebuilt
    conns = res["connections"]
    assert "Set1" in conns
    assert conns["Set1"]["main"][0][0]["node"] == "Set2"

def test_optimizer_optimize_recipe():
    opt = WorkflowOptimizer()
    recipe = Recipe(name="R", steps=[
        RecipeStep(id="s1", template="set", params={"name": "a", "value": "1"}),
        RecipeStep(id="s2", template="set", params={"name": "b", "value": "2"}, connections_from=["s1"])
    ])
    
    res = opt.optimize(recipe)
    assert len(res.steps) == 1
    assert res.steps[0].template == "set_multi"
