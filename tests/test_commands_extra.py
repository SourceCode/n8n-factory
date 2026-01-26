import pytest
import os
import requests
from unittest.mock import patch, MagicMock, mock_open
from n8n_factory.commands.publish import publish_workflow
from n8n_factory.commands.inspect import inspect_template
from n8n_factory.commands.examples import examples_command
from n8n_factory.commands.watch import RecipeHandler
from n8n_factory.models import Recipe, RecipeStep

@pytest.fixture
def mock_recipe():
    return Recipe(name="Test", steps=[RecipeStep(id="s1", template="webhook", params={"path": "test", "method": "GET", "uuid": "u1"})])

def test_publish_workflow_success(mock_recipe, capsys):
    with patch.dict(os.environ, {"N8N_URL": "http://n8n", "N8N_API_KEY": "key"}):
        with patch("requests.post") as mock_post:
            with patch("n8n_factory.commands.publish.WorkflowAssembler") as mock_asm:
                mock_post.return_value.status_code = 200
                mock_post.return_value.json.return_value = {"id": "123", "active": True}
                mock_asm.return_value.assemble.return_value = {
                    "name": "Test Workflow",
                    "nodes": [],
                    "connections": {},
                    "meta": {}
                }

                publish_workflow(mock_recipe, "templates")

                assert "Success" in capsys.readouterr().out

def test_examples_command_copy_errors(tmp_path, capsys):
    # Ensure examples dir exists for the test
    ex_dir = tmp_path / "examples"
    ex_dir.mkdir()
    
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        examples_command("copy")
        assert "Specify example name" in capsys.readouterr().out
        
        examples_command("copy", "missing.yaml")
        assert "not found" in capsys.readouterr().out
        
        (ex_dir / "ex.yaml").touch()
        # Create destination file to trigger "already exists"
        (tmp_path / "ex.yaml").touch()
        
        examples_command("copy", "ex.yaml")
        assert "already exists" in capsys.readouterr().out
    finally:
        os.chdir(cwd)

def test_watch_ignore_patterns(tmp_path):
    (tmp_path / ".n8nignore").write_text("*.tmp\nignore_me.yaml", encoding="utf-8")
    
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        handler = RecipeHandler(str(tmp_path / "recipe.yaml"), "templates")
        
        with patch("os.path.relpath", return_value="ignore_me.yaml"):
            assert handler._is_ignored("/abs/path/ignore_me.yaml") is True
            
        with patch("os.path.relpath", return_value="recipe.yaml"):
            assert handler._is_ignored("/abs/path/recipe.yaml") is False
    finally:
        os.chdir(cwd)