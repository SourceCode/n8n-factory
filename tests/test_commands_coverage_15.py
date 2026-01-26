import pytest
import os
import yaml
from unittest.mock import MagicMock, patch
from n8n_factory.utils import load_recipe
from n8n_factory.optimizer import WorkflowOptimizer
from n8n_factory.commands.inspect import inspect_template
from n8n_factory.models import Recipe, RecipeStep
from n8n_factory.commands.publish import publish_workflow

# --- Utils Tests ---
def test_load_recipe_dict_import(tmp_path):
    sub = tmp_path / "sub.yaml"
    sub.write_text('name: Sub\nsteps:\n  - id: s1\n    template: t', encoding="utf-8")
    
    base = tmp_path / "base.yaml"
    # Import as dict
    data = {
        "name": "Base",
        "imports": [{"path": "sub.yaml", "namespace": "ns"}]
    }
    with open(base, "w") as f:
        yaml.dump(data, f)
        
    recipe = load_recipe(str(base))
    assert len(recipe.steps) == 1
    assert recipe.steps[0].id == "ns_s1"

def test_load_recipe_empty_import(tmp_path):
    base = tmp_path / "base.yaml"
    # Empty string import and empty dict
    data = {
        "name": "Base",
        "imports": ["", {}]
    }
    with open(base, "w") as f:
        yaml.dump(data, f)
    
    with pytest.raises(SystemExit):
        load_recipe(str(base))

# --- Optimizer Tests ---
def test_optimizer_used_vars(caplog):
    import logging
    caplog.set_level(logging.WARNING)
    opt = WorkflowOptimizer()
    recipe = Recipe(name="R", steps=[
        RecipeStep(id="s1", template="set", params={"name": "x", "value": "1"}),
        RecipeStep(id="s2", template="code", params={"c": "={{ $json.x }}"})
    ])
    
    opt.optimize(recipe)
    # x is used, so no warning about x
    assert "Unused variables" not in caplog.text

# --- Publish Tests ---
def test_publish_partial_env(capsys):
    # URL set, Key missing
    with patch.dict(os.environ, {"N8N_URL": "http://u"}, clear=True):
        publish_workflow(Recipe(name="R", steps=[]), "t", json_output=False)
    assert "N8N_URL and N8N_API_KEY env vars must be set" in capsys.readouterr().out
