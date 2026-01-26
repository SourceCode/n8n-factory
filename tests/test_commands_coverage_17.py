import pytest
import time
from unittest.mock import MagicMock, patch
from n8n_factory.commands.inspect import inspect_template
from n8n_factory.commands.watch import RecipeHandler
from n8n_factory.optimizer import WorkflowOptimizer
from n8n_factory.models import Recipe, RecipeStep

# --- Inspect Tests ---
def test_inspect_invalid_json(tmp_path, capsys):
    d = tmp_path / "templates"
    d.mkdir()
    p = d / "bad.json"
    p.write_text("{ invalid", encoding="utf-8")
    
    inspect_template("bad", str(d), json_output=False)
    captured = capsys.readouterr()
    assert "Invalid JSON" in captured.out

# --- Watch Tests ---
@patch("n8n_factory.commands.watch.console")
@patch("n8n_factory.commands.watch.load_recipe")
@patch("n8n_factory.commands.watch.WorkflowAssembler")
def test_watch_handler_modified(mock_asm, mock_load, mock_console, tmp_path):
    p = tmp_path / "r.yaml"
    p.touch()
    
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        handler = RecipeHandler(str(p), "tmpl")
        
        # Mock event
        event = MagicMock()
        event.src_path = str(p)
        
        handler.on_modified(event)
        
        mock_load.assert_called()
        mock_asm.return_value.assemble.assert_called()
        assert "Rebuild Successful" in str(mock_console.print.call_args_list)
    finally:
        os.chdir(cwd)

@patch("n8n_factory.commands.watch.console")
def test_watch_handler_ignore(mock_console, tmp_path):
    p = tmp_path / "r.yaml"
    p.touch()
    (tmp_path / ".n8nignore").write_text("ignored.yaml", encoding="utf-8")
    
    os_chdir = os.getcwd()
    os.chdir(tmp_path)
    try:
        handler = RecipeHandler(str(p), "tmpl")
        event = MagicMock()
        event.src_path = str(tmp_path / "ignored.yaml")
        
        handler.on_modified(event)
        # Should return early, no print
        assert mock_console.print.call_count == 0
    finally:
        os.chdir(os_chdir)

import os

# --- Optimizer Tests ---
def test_optimizer_constant_folding(caplog):
    import logging
    caplog.set_level(logging.INFO)
    opt = WorkflowOptimizer()
    recipe = Recipe(name="R", steps=[
        RecipeStep(id="if1", template="if", params={"left": "a", "right": "a", "operator": "equal"}),
        RecipeStep(id="if2", template="if", params={"left": "a", "right": "b", "operator": "equal"})
    ])
    
    opt.optimize(recipe)
    assert "IF node 'if1' is always TRUE" in caplog.text
    assert "IF node 'if2' is always FALSE" in caplog.text

def test_optimizer_prune_code(caplog):
    import logging
    caplog.set_level(logging.INFO)
    opt = WorkflowOptimizer()
    recipe = Recipe(name="R", steps=[
        RecipeStep(id="c1", template="code", params={"code": "return items;"}),
        RecipeStep(id="c2", template="code", params={"code": "real code"})
    ])
    
    res = opt.optimize(recipe)
    # c1 should be removed
    ids = [s.id for s in res.steps]
    assert "c1" not in ids
    assert "c2" in ids
    assert "Pruning empty code node 'c1'" in caplog.text
