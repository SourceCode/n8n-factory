import pytest
import json
import os
import shutil
from unittest.mock import MagicMock, patch
from n8n_factory.commands.health import health_command
from n8n_factory.commands.telemetry_cmd import telemetry_export_command
from n8n_factory.commands.tree import tree_command
from n8n_factory.commands.profile import profile_command
from n8n_factory.models import Recipe, RecipeStep

# --- Health Tests ---
def test_health_json(capsys):
    with patch("shutil.which", return_value="docker"):
        with patch("os.path.isdir", return_value=True):
            with patch("os.path.exists", return_value=True):
                health_command(json_output=True)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["healthy"] is True

@patch("n8n_factory.commands.health.console")
def test_health_console_unhealthy(mock_console):
    with patch("shutil.which", return_value=None):
        health_command(json_output=False)
    # Check for failure message
    found = False
    for call in mock_console.print.call_args_list:
        if "System has issues" in str(call):
            found = True
    assert found

# --- Telemetry Cmd Tests ---
@patch("n8n_factory.commands.telemetry_cmd.load_telemetry")
def test_telemetry_cmd(mock_load, capsys):
    mock_load.return_value = [{"id": 1}]
    telemetry_export_command(json_output=True)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert len(data) == 1

# --- Tree Tests ---
@patch("n8n_factory.commands.tree.console")
def test_tree_full(mock_console):
    recipe = Recipe(
        name="R",
        globals={"g": 1},
        imports=["i.yaml"],
        steps=[
            RecipeStep(id="s1", template="t", disabled=True),
            RecipeStep(id="s2", template="t", connections_from=["s1"])
        ]
    )
    tree_command(recipe)
    mock_console.print.assert_called()

# --- Profile Tests ---
@patch("n8n_factory.commands.profile.console")
def test_profile_not_found(mock_console, tmp_path):
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        profile_command("missing")
        assert "not found" in str(mock_console.print.call_args_list)
    finally:
        os.chdir(cwd)

@patch("n8n_factory.commands.profile.console")
def test_profile_success(mock_console, tmp_path):
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        with open(".env.dev", "w") as f: f.write("ENV=dev")
        profile_command("dev")
        assert os.path.exists(".env")
        with open(".env") as f: assert "ENV=dev" in f.read()
    finally:
        os.chdir(cwd)

@patch("n8n_factory.commands.profile.console")
def test_profile_error(mock_console, tmp_path):
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        with open(".env.dev", "w") as f: f.write("ENV=dev")
        with patch("shutil.copy", side_effect=Exception("Copy fail")):
            profile_command("dev")
        assert "Failed" in str(mock_console.print.call_args_list)
    finally:
        os.chdir(cwd)
