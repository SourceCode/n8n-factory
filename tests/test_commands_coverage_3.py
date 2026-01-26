import pytest
import json
import os
import subprocess
from unittest.mock import MagicMock, patch, mock_open
from n8n_factory.operator import SystemOperator
from n8n_factory.telemetry import log_event, track_command, load_telemetry
from n8n_factory.commands.validate import validate_recipe
from n8n_factory.normalizer import WorkflowNormalizer
from n8n_factory.models import Recipe, RecipeStep

# --- Operator Tests ---
@pytest.fixture
def operator():
    return SystemOperator()

@patch("n8n_factory.operator.subprocess.run")
def test_operator_get_logs(mock_run, operator):
    mock_run.return_value = MagicMock(stdout="line1\nline2")
    logs = operator.get_logs("n8n")
    assert "line1" in logs
    mock_run.assert_called()

@patch("n8n_factory.operator.subprocess.run")
def test_operator_run_cmd_error(mock_run, operator):
    mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="error")
    with pytest.raises(RuntimeError):
        operator._run_cmd(["cmd"])

@patch("n8n_factory.operator.subprocess.run")
def test_operator_db_query(mock_run, operator):
    # Mocking postgres COPY output
    mock_run.return_value = MagicMock(stdout='{"id": 1}\n{"id": 2}')
    res = operator.run_db_query("SELECT * FROM table")
    assert len(res) == 2
    assert res[0]["id"] == 1

@patch("n8n_factory.operator.subprocess.run")
def test_operator_redis(mock_run, operator):
    mock_run.return_value = MagicMock(stdout="PONG")
    res = operator.inspect_redis("PING")
    assert res == "PONG"

@patch("n8n_factory.operator.subprocess.run")
def test_operator_exec_id(mock_run, operator):
    mock_run.return_value = MagicMock(stdout="Done")
    res = operator.execute_workflow(workflow_id="1")
    assert res == "Done"
    args = mock_run.call_args[0][0]
    assert "--id" in args

@patch("n8n_factory.operator.subprocess.run")
def test_operator_exec_file(mock_run, operator):
    mock_run.return_value = MagicMock(stdout="Done")
    res = operator.execute_workflow(file_path="w.json")
    assert res == "Done"
    # Should check for docker cp call too
    assert mock_run.call_count == 2 # cp + exec

@patch("n8n_factory.operator.subprocess.run")
def test_operator_webhook(mock_run, operator):
    mock_run.return_value = MagicMock(stdout="OK")
    res = operator.trigger_webhook("POST", "http://localhost", {"a": 1})
    assert res == "OK"

@patch("n8n_factory.operator.SystemOperator.get_logs")
def test_operator_analyze(mock_logs, operator):
    mock_logs.return_value = "INFO start\nERROR failed\nWARN retry"
    res = operator.analyze_logs()
    assert res["errors"] == 1
    assert res["warnings"] == 1
    assert res["status"] == "Unhealthy"

# --- Telemetry Tests ---
@patch("n8n_factory.telemetry.load_telemetry")
@patch("n8n_factory.telemetry.save_telemetry")
def test_telemetry_log(mock_save, mock_load):
    mock_load.return_value = []
    log_event("test", {"p": 1}, "success", 0.1)
    mock_save.assert_called()
    events = mock_save.call_args[0][0]
    assert len(events) == 1
    assert events[0]["command"] == "test"

@patch("n8n_factory.telemetry.log_event")
def test_telemetry_decorator(mock_log):
    @track_command("test_cmd")
    def my_func(arg):
        return arg
    
    my_func("val")
    mock_log.assert_called()
    assert mock_log.call_args[0][0] == "test_cmd"

@patch("n8n_factory.telemetry.log_event")
def test_telemetry_decorator_error(mock_log):
    @track_command("fail_cmd")
    def my_func():
        raise ValueError("boom")
    
    with pytest.raises(ValueError):
        my_func()
    
    mock_log.assert_called()
    assert mock_log.call_args[0][2] == "error"

def test_load_telemetry_no_file():
    with patch("os.path.exists", return_value=False):
        assert load_telemetry() == []

# --- Validate Tests ---
@patch("n8n_factory.commands.validate.WorkflowAssembler")
@patch("n8n_factory.commands.validate.console")
def test_validate_success(mock_console, mock_asm, capsys):
    recipe = Recipe(name="R", steps=[RecipeStep(id="s1", template="t")])
    validate_recipe(recipe, "tmpl", json_output=True)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["valid"] is True
    assert data["checks"]["assembly"]["status"] == "passed"

@patch("n8n_factory.commands.validate.WorkflowAssembler")
def test_validate_fail(mock_asm, capsys):
    mock_asm.return_value.assemble.side_effect = ValueError("Bad template")
    recipe = Recipe(name="R", steps=[])
    validate_recipe(recipe, "tmpl", json_output=True)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["valid"] is False
    assert "Bad template" in data["checks"]["assembly"]["error"]

def test_validate_env(capsys):
    recipe = Recipe(name="R", steps=[RecipeStep(id="s1", template="t", params={"k": "$env.MISSING"})])
    # Ensure env var is missing
    if "MISSING" in os.environ: del os.environ["MISSING"]
    
    # Mock assembler to pass
    with patch("n8n_factory.commands.validate.WorkflowAssembler"):
        validate_recipe(recipe, "tmpl", check_env=True, json_output=True)
        
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "MISSING" in data["checks"]["environment"]["missing"]

def test_validate_js(capsys):
    recipe = Recipe(name="R", steps=[RecipeStep(id="s1", template="code", params={"code": "if (a { return 1;"})])
    with patch("n8n_factory.commands.validate.WorkflowAssembler"):
        validate_recipe(recipe, "tmpl", check_js=True, json_output=True)
        
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "Unbalanced braces" in str(data["checks"]["javascript"]["issues"])

# --- Normalizer Tests ---
def test_normalizer_json():
    norm = WorkflowNormalizer()
    wf = {
        "nodes": [
            {"name": "B", "type": "n"},
            {"name": "A", "type": "n"} # Missing position
        ],
        "connections": {
            "B": {},
            "A": {}
        }
    }
    res = norm.normalize_json(wf)
    nodes = res["nodes"]
    assert nodes[0]["name"] == "A"
    assert nodes[1]["name"] == "B"
    assert "position" in nodes[0]
    
    # Check connections sorted
    keys = list(res["connections"].keys())
    assert keys == ["A", "B"]

def test_normalizer_recipe():
    norm = WorkflowNormalizer()
    r = Recipe(name="R", steps=[])
    res = norm.normalize_recipe(r)
    assert res.name == "R"
