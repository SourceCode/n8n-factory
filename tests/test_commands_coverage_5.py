import pytest
import json
import os
import shutil
from unittest.mock import MagicMock, patch, mock_open
from n8n_factory.commands.diff import diff_recipe
from n8n_factory.commands.lint import lint_recipe
from n8n_factory.commands.doc import doc_command
from n8n_factory.commands.project import project_init_command
from n8n_factory.models import Recipe, RecipeStep
from n8n_factory.operator import SystemOperator
import subprocess

# --- Diff Tests ---
@patch("n8n_factory.commands.diff.WorkflowAssembler")
@patch("n8n_factory.commands.diff.load_recipe")
@patch("n8n_factory.commands.diff.DeepDiff")
def test_diff_recipe_json_target(mock_dd, mock_load, mock_asm, tmp_path, capsys):
    mock_load.return_value = Recipe(name="R", steps=[])
    mock_asm.return_value.assemble.return_value = {"nodes": []}
    
    # Mock DeepDiff instance to behave like a dict AND have to_json
    mock_diff_instance = MagicMock()
    mock_diff_instance.__getitem__.side_effect = lambda k: {"values_changed": {}}.get(k)
    mock_diff_instance.get.side_effect = lambda k, d=None: {"values_changed": {}}.get(k, d)
    mock_diff_instance.to_json.return_value = '{"values_changed": ...}'
    # Make it truthy
    mock_diff_instance.__bool__.return_value = True
    
    mock_dd.return_value = mock_diff_instance
    
    target_file = tmp_path / "target.json"
    with open(target_file, "w") as f:
        json.dump({"nodes": []}, f)
        
    diff_recipe("r.yaml", str(target_file), "tmpl", json_output=True)
    
    captured = capsys.readouterr()
    # The output is from diff.to_json()
    assert "values_changed" in captured.out

@patch("n8n_factory.commands.diff.WorkflowAssembler")
@patch("n8n_factory.commands.diff.load_recipe")
def test_diff_recipe_invalid_target(mock_load, mock_asm, capsys):
    mock_load.return_value = Recipe(name="R", steps=[])
    diff_recipe("r.yaml", "target.txt", "tmpl", json_output=True)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "error" in data

@patch("n8n_factory.commands.diff.WorkflowAssembler")
@patch("n8n_factory.commands.diff.load_recipe")
@patch("n8n_factory.commands.diff.DeepDiff")
def test_diff_recipe_summary(mock_dd, mock_load, mock_asm, capsys):
    mock_load.return_value = Recipe(name="R", steps=[])
    mock_dd.return_value = {"dictionary_item_added": ["root['a']"]}
    
    diff_recipe("r.yaml", "t.yaml", "tmpl", summary=True, json_output=True)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "diff_found"
    assert data["counts"]["added"] == 1

@patch("n8n_factory.commands.diff.WorkflowAssembler")
@patch("n8n_factory.commands.diff.load_recipe")
@patch("n8n_factory.commands.diff.console")
def test_diff_recipe_html(mock_console, mock_load, mock_asm):
    mock_load.return_value = Recipe(name="R", steps=[])
    diff_recipe("r.yaml", "t.yaml", "tmpl", html_output="diff.html")
    mock_console.save_html.assert_called_with("diff.html")

# --- Lint Tests ---
@patch("n8n_factory.commands.lint.WorkflowAssembler")
def test_lint_strict_fail(mock_asm, capsys):
    # Step ID not snake case and no description
    recipe = Recipe(name="R", steps=[RecipeStep(id="BadID", template="t")], description="")
    
    with pytest.raises(SystemExit):
        lint_recipe(recipe, "tmpl", strict=True, json_output=True)
        
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["valid"] is False
    assert len(data["errors"]) > 0

@patch("n8n_factory.commands.lint.WorkflowAssembler")
def test_lint_pass(mock_asm, capsys):
    recipe = Recipe(name="R", description="Good", steps=[RecipeStep(id="good_id", template="t", description="desc")])
    lint_recipe(recipe, "tmpl", strict=True, json_output=True)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["valid"] is True

# --- Doc Tests ---
def test_doc_command_prompt(capsys):
    recipe = Recipe(name="R", steps=[RecipeStep(id="s1", template="t", description="d")])
    doc_command(recipe, json_output=True, prompt_mode=True)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "Create an n8n workflow" in data["markdown"]
    assert "Purpose: d" in data["markdown"]

def test_doc_command_standard(capsys):
    recipe = Recipe(name="R", steps=[RecipeStep(id="s1", template="webhook")])
    doc_command(recipe, json_output=True)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "# R" in data["markdown"]
    assert "webhook" in data["markdown"]

# --- Project Tests ---
def test_project_init(tmp_path, capsys):
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        project_init_command(json_output=True)
        assert os.path.exists("recipes")
        assert os.path.exists(".env.example")
        
        # Test force
        with open(".env.example", "w") as f: f.write("OLD")
        project_init_command(force=True, json_output=True)
        with open(".env.example", "r") as f: assert "N8N_URL" in f.read()
    finally:
        os.chdir(cwd)

# --- Operator Error Tests ---
@patch("n8n_factory.operator.subprocess.run")
def test_operator_execute_error(mock_run):
    op = SystemOperator()
    mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="Fail")
    res = op.execute_workflow("1")
    assert "Execution failed" in res

@patch("n8n_factory.operator.subprocess.run")
def test_operator_webhook_error(mock_run):
    op = SystemOperator()
    mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="Fail")
    res = op.trigger_webhook("GET", "url")
    assert "Webhook trigger failed" in res
