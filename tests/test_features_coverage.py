import pytest
import sys
import os
import yaml
import json
from unittest.mock import patch, MagicMock
from n8n_factory.cli import main
from n8n_factory.simulator import WorkflowSimulator

# Test simulate --export-html
def test_cli_simulate_html(tmp_path, capsys):
    recipe_path = tmp_path / "recipe.yaml"
    recipe_data = {
        "name": "HTML Sim Test",
        "steps": [{"id": "s1", "template": "webhook", "params": {"path": "p", "method": "m"}}]
    }
    with open(recipe_path, "w") as f:
        yaml.dump(recipe_data, f)
    
    html_output = tmp_path / "report.html"
    
    # We patch WorkflowSimulator in cli.py where it is instantiated
    with patch("n8n_factory.cli.WorkflowSimulator") as MockSim:
        instance = MockSim.return_value
        # Mock simulate to return some data so generate_html_report receives it
        instance.simulate.return_value = [{"step": "s1", "output": []}]
        
        with patch.object(sys, 'argv', ["n8n-factory", "simulate", str(recipe_path), "--export-html", str(html_output)]):
            main()
        
        # Verify simulate was called
        instance.simulate.assert_called()
        # Verify generate_html_report was called with the history and output path
        instance.generate_html_report.assert_called_once_with(instance.simulate.return_value, str(html_output))

# Unit test for generate_html_report
def test_generate_html_report_content(tmp_path):
    sim = WorkflowSimulator()
    history = [{
        "step_id": "step1",
        "template": "webhook",
        "input": [{"json": {"a": 1}}],
        "output": [{"json": {"a": 1}}]
    }]
    output = tmp_path / "report.html"
    sim.generate_html_report(history, str(output))
    
    assert output.exists()
    content = output.read_text("utf-8")
    assert "Simulation Report" in content
    assert "step1" in content
    assert "webhook" in content
    assert '"a": 1' in content

# Unit test for export_csv
def test_export_csv_content(tmp_path):
    sim = WorkflowSimulator()
    history = [{
        "step_id": "step1",
        "template": "webhook",
        "input": [{"json": {"a": 1}}],
        "output": [{"json": {"a": 1}}]
    }]
    output = tmp_path / "report.csv"
    sim.export_csv(history, str(output))
    
    assert output.exists()
    content = output.read_text("utf-8")
    assert "step_id,template,input,output,error" in content
    assert "step1,webhook" in content

# Test queue add
def test_queue_add(capsys):
    # Patch QueueManager in the schedule command module
    with patch("n8n_factory.commands.schedule.QueueManager") as MockQM:
        instance = MockQM.return_value
        
        with patch.object(sys, 'argv', ["n8n-factory", "queue", "add", "my_workflow", "--data", '{"a":1}']):
            main()
        
        instance.enqueue.assert_called_once_with("my_workflow", inputs={"a": 1}, mode="id")
        captured = capsys.readouterr()
        assert "Job added to queue" in captured.out

# Test queue list
def test_queue_list(capsys):
    with patch("n8n_factory.commands.schedule.QueueManager") as MockQM:
        instance = MockQM.return_value
        instance.list_jobs.return_value = [{"workflow": "wf1", "mode": "id", "inputs": {}}]
        
        with patch.object(sys, 'argv', ["n8n-factory", "queue", "list"]):
            main()
            
        instance.list_jobs.assert_called_once()
        captured = capsys.readouterr()
        assert "wf1" in captured.out

# Test queue clear
def test_queue_clear(capsys):
    with patch("n8n_factory.commands.schedule.QueueManager") as MockQM:
        instance = MockQM.return_value
        
        with patch.object(sys, 'argv', ["n8n-factory", "queue", "clear"]):
            main()
            
        instance.clear.assert_called_once()
        captured = capsys.readouterr()
        assert "Queue cleared" in captured.out
