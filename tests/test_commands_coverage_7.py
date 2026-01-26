import pytest
import json
from unittest.mock import MagicMock, patch
from n8n_factory.cli import main

# --- Ops CLI Tests ---
@patch("n8n_factory.cli.SystemOperator")
def test_cli_ops_logs(mock_op):
    mock_op.return_value.get_logs.return_value = "log data"
    with patch("sys.argv", ["n8n-factory", "ops", "logs", "--service", "n8n", "--json"]):
        main()
    mock_op.return_value.get_logs.assert_called_with("n8n", 100)

@patch("n8n_factory.cli.SystemOperator")
def test_cli_ops_db(mock_op):
    mock_op.return_value.run_db_query.return_value = [{"id": 1}]
    with patch("sys.argv", ["n8n-factory", "ops", "db", "-q", "SELECT 1", "--json"]):
        main()
    mock_op.return_value.run_db_query.assert_called_with("SELECT 1")

@patch("n8n_factory.cli.SystemOperator")
def test_cli_ops_redis(mock_op):
    mock_op.return_value.inspect_redis.return_value = "PONG"
    with patch("sys.argv", ["n8n-factory", "ops", "redis", "-c", "INFO", "--json"]):
        main()
    mock_op.return_value.inspect_redis.assert_called_with("INFO")

@patch("n8n_factory.cli.SystemOperator")
def test_cli_ops_exec(mock_op):
    mock_op.return_value.execute_workflow.return_value = "Done"
    with patch("sys.argv", ["n8n-factory", "ops", "exec", "--id", "1", "--json"]):
        main()
    mock_op.return_value.execute_workflow.assert_called_with("1", None)

@patch("n8n_factory.cli.SystemOperator")
def test_cli_ops_webhook(mock_op):
    mock_op.return_value.trigger_webhook.return_value = "OK"
    with patch("sys.argv", ["n8n-factory", "ops", "webhook", "url", "-d", '{"a":1}', "--json"]):
        main()
    mock_op.return_value.trigger_webhook.assert_called()

@patch("n8n_factory.cli.SystemOperator")
def test_cli_ops_analyze(mock_op):
    mock_op.return_value.analyze_logs.return_value = {"status": "ok"}
    with patch("sys.argv", ["n8n-factory", "ops", "analyze-logs", "--json"]):
        main()
    mock_op.return_value.analyze_logs.assert_called()

# --- Template Extract ---
@patch("n8n_factory.cli.template_extract_command")
def test_cli_template_extract(mock_cmd):
    # This assumes template_extract_command is imported in cli.py
    # If not, NameError will happen, revealing a bug.
    try:
        with patch("sys.argv", ["n8n-factory", "template", "extract", "w.json", "n1"]):
            main()
        mock_cmd.assert_called()
    except NameError:
        pytest.fail("template_extract_command not defined/imported in cli.py")

# --- Policy ---
@patch("n8n_factory.cli.load_recipe")
@patch("n8n_factory.cli.policy_check_command")
def test_cli_policy(mock_cmd, mock_load):
    # If policy_check_command is missing, this will fail
    try:
        with patch("sys.argv", ["n8n-factory", "policy", "r.yaml"]):
            main()
        mock_cmd.assert_called()
    except NameError:
        pytest.fail("policy_check_command not defined/imported in cli.py")

# --- Security CLI ---
@patch("n8n_factory.cli.load_recipe")
@patch("n8n_factory.cli.security_command")
def test_cli_security(mock_cmd, mock_load):
    with patch("sys.argv", ["n8n-factory", "security", "r.yaml"]):
        main()
    mock_cmd.assert_called()
