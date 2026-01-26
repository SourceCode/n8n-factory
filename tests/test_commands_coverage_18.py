import pytest
import subprocess
from unittest.mock import patch, MagicMock
from n8n_factory.operator import SystemOperator
from n8n_factory.commands.inspect import inspect_template

def test_operator_error_no_stderr():
    op = SystemOperator()
    with patch("n8n_factory.operator.subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr=None)
        res = op.execute_workflow("1")
        assert "Execution failed" in res
        # Check that str(e) was used in logger/error?
        # We can't easily check internal variable but we hit the branch.

def test_inspect_path_not_exists(tmp_path, capsys):
    # Test line 11: if not os.path.exists(template_path)
    # where template_path is "missing" (relative)
    # It enters block, constructs path in templates dir.
    # Then line 13: if not os.path.exists(path) -> True.
    # Logs error.
    
    inspect_template("missing", str(tmp_path), json_output=False)
    assert "Error" in capsys.readouterr().out
