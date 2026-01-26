import pytest
import json
import os
from unittest.mock import MagicMock, patch, mock_open
from n8n_factory.cli import main

@patch("n8n_factory.cli.inspect_template")
def test_cli_inspect(mock_inspect):
    with patch("sys.argv", ["n8n-factory", "inspect", "webhook"]):
        main()
    mock_inspect.assert_called()

def test_cli_inspect_integration(tmp_path, capsys):
    # Integration test without mocking inspect_template (covers inspect.py)
    tmpl_dir = tmp_path / "templates"
    tmpl_dir.mkdir()
    (tmpl_dir / "t.json").write_text('{"type": "test", "parameters": {"a": 1}}', encoding="utf-8")
    
    with patch("sys.argv", ["n8n-factory", "inspect", "t", "-t", str(tmpl_dir)]):
        main()
    
    out = capsys.readouterr().out
    assert "test" in out
    
    with patch("sys.argv", ["n8n-factory", "inspect", "t", "-t", str(tmpl_dir), "--json"]):
        main()
    out = capsys.readouterr().out
    assert '"a": 1' in out

@patch("n8n_factory.cli.load_recipe")
@patch("n8n_factory.cli.policy_check_command")
def test_cli_policy_call(mock_policy, mock_load):
    with patch("sys.argv", ["n8n-factory", "policy", "r.yaml"]):
        main()
    mock_policy.assert_called()

@patch("n8n_factory.cli.template_extract_command")
def test_cli_extract_call(mock_ext):
    with patch("sys.argv", ["n8n-factory", "template", "extract", "w.json", "n1"]):
        main()
    mock_ext.assert_called()

@patch("n8n_factory.cli.template_new_command")
def test_cli_template_new_call(mock_new):
    with patch("sys.argv", ["n8n-factory", "template", "new", "--name", "n", "--type", "t"]):
        main()
    mock_new.assert_called()
