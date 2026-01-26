import pytest
import os
import csv
from unittest.mock import patch, MagicMock
from n8n_factory.cli import main
from n8n_factory.operator import SystemOperator

def test_cli_help(capsys):
    with patch("sys.argv", ["n8n-factory", "--help"]):
        with pytest.raises(SystemExit):
            main()
    captured = capsys.readouterr()
    assert "usage:" in captured.out

def test_cli_simulate_csv(tmp_path):
    recipe = tmp_path / "r.yaml"
    recipe.write_text('name: R\nsteps:\n  - id: s1\n    template: no_op', encoding="utf-8")
    out = tmp_path / "out.csv"
    
    with patch("n8n_factory.cli.load_recipe") as mock_load:
        # We need a real-ish recipe object or mock
        from n8n_factory.models import Recipe, RecipeStep
        mock_load.return_value = Recipe(name="R", steps=[RecipeStep(id="s1", template="no_op")])
        
        # We need WorkflowSimulator to actually write CSV or we mock it?
        # cli.py calls simulator.export_csv
        # Let's mock WorkflowSimulator
        with patch("n8n_factory.cli.WorkflowSimulator") as MockSim:
            MockSim.return_value.simulate.return_value = [{"step": "s1"}]
            with patch("sys.argv", ["n8n-factory", "simulate", str(recipe), "--export-csv", str(out)]):
                main()
            MockSim.return_value.export_csv.assert_called()

def test_operator_analyze_crash():
    op = SystemOperator()
    with patch("n8n_factory.operator.SystemOperator.get_logs", return_value="crashed\nERROR"):
        res = op.analyze_logs()
    assert res["crashes_detected"] is True
    assert res["errors"] == 1
    assert res["status"] == "Unhealthy"
