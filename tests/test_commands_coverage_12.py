import pytest
import os
from unittest.mock import MagicMock, patch
from n8n_factory.commands.publish import publish_workflow
from n8n_factory.commands.info import info_command
from n8n_factory.operator import SystemOperator
from n8n_factory.models import Recipe

# --- Publish Tests ---
def test_publish_missing_env_console(capsys):
    with patch.dict(os.environ, {}, clear=True):
        publish_workflow(Recipe(name="R", steps=[]), "t", json_output=False)
    assert "N8N_URL and N8N_API_KEY env vars must be set" in capsys.readouterr().out

def test_publish_missing_env_json(capsys):
    with patch.dict(os.environ, {}, clear=True):
        publish_workflow(Recipe(name="R", steps=[]), "t", json_output=True)
    assert '"error":' in capsys.readouterr().out

def test_publish_activation_retry(capsys):
    # Test that it tries to activate if initial create didn't
    with patch.dict(os.environ, {"N8N_URL": "http://u", "N8N_API_KEY": "k"}):
        with patch("n8n_factory.commands.publish.WorkflowAssembler") as mock_asm:
            mock_asm.return_value.assemble.return_value = {"name": "R", "nodes": [], "connections": {}, "meta": {}}
            with patch("requests.post") as mock_post:
                # 1. Create (active=False)
                # 2. Activate
                mock_post.side_effect = [
                    MagicMock(status_code=200, json=lambda: {"id": "1", "active": False}),
                    MagicMock(status_code=200)
                ]
                
                publish_workflow(Recipe(name="R", steps=[]), "t", activate=True, json_output=False)
                
    assert "Workflow activated" in capsys.readouterr().out

# --- Info Tests ---
@patch("n8n_factory.commands.info.load_recipe")
def test_info_dependencies(mock_load, capsys):
    mock_load.return_value = Recipe(name="R", steps=[])
    # Mock return value doesn't have imports usually unless we set it
    mock_load.return_value.imports = ["imp1"]
    
    info_command("r.yaml", dependencies=True, json_output=False)
    captured = capsys.readouterr()
    assert "Templates Used" in captured.out
    assert "Imports: 1" in captured.out

# --- Operator Tests ---
@patch("n8n_factory.operator.subprocess.run")
def test_operator_exec_file_cp(mock_run):
    op = SystemOperator()
    mock_run.return_value = MagicMock(stdout="Done")
    
    op.execute_workflow(file_path="w.json")
    
    # Check calls: cp then exec
    assert mock_run.call_count == 2
    args0 = mock_run.call_args_list[0][0][0]
    assert args0[0] == "docker"
    assert args0[1] == "cp"
    
    args1 = mock_run.call_args_list[1][0][0]
    assert args1[6] == "execute"
    assert "--file" in args1