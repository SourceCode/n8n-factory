import pytest
import os
from unittest.mock import patch, MagicMock, mock_open
from n8n_factory.commands.login import login_command
from n8n_factory.commands.project import project_init_command
from n8n_factory.operator import SystemOperator

# --- Login Tests ---
def test_login_existing_env(tmp_path, capsys):
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        with open(".env", "w") as f:
            f.write("N8N_URL=old\nOTHER=1")
            
        with patch("rich.prompt.Prompt.ask", side_effect=["new_url", "new_key"]):
            login_command()
            
        with open(".env") as f:
            content = f.read()
            assert "N8N_URL=new_url" in content
            assert "N8N_API_KEY=new_key" in content
            assert "OTHER=1" in content
    finally:
        os.chdir(cwd)

def test_login_append(tmp_path, capsys):
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        with open(".env", "w") as f:
            f.write("OTHER=1") # No N8N vars
            
        with patch("rich.prompt.Prompt.ask", side_effect=["u", "k"]):
            login_command()
            
        with open(".env") as f:
            content = f.read()
            assert "N8N_URL=u" in content
            assert "N8N_API_KEY=k" in content
    finally:
        os.chdir(cwd)

# --- Project Tests ---
def test_project_init_exists(tmp_path, capsys):
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        # Run once
        project_init_command(json_output=False)
        # Run again
        project_init_command(json_output=False)
        assert "Project already initialized" in capsys.readouterr().out
    finally:
        os.chdir(cwd)

# --- Operator Tests ---
def test_operator_logs_fail():
    op = SystemOperator()
    with patch("n8n_factory.operator.subprocess.run", side_effect=RuntimeError("Docker fail")):
        logs = op.get_logs("n8n")
        assert "Failed to get logs" in logs