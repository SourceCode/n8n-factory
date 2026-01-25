import pytest
import os
import yaml
from n8n_factory.utils import load_recipe

def test_load_recipe_with_env_config(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    
    (root / "recipe.yaml").write_text('name: "EnvTest"\nsteps: []', encoding="utf-8")
    
    conf_dir = root / "config"
    conf_dir.mkdir()
    (conf_dir / "dev.yaml").write_text('api_key: "dev_secret"', encoding="utf-8")
    
    # Run from root
    cwd = os.getcwd()
    os.chdir(root)
    try:
        recipe = load_recipe("recipe.yaml", env_name="dev")
        assert recipe.globals["api_key"] == "dev_secret"
    finally:
        os.chdir(cwd)

def test_load_recipe_import_error(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    (root / "recipe.yaml").write_text('name: "ImpTest"\nimports: ["missing.yaml"]\nsteps: []', encoding="utf-8")
    
    with pytest.raises(SystemExit):
        load_recipe(str(root / "recipe.yaml"))

