import pytest
import os
import yaml
from unittest.mock import patch, MagicMock
from n8n_factory.cli import main, load_config

# --- CLI Config Tests ---
def test_load_config_success(tmp_path):
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        with open(".n8n-factory.yaml", "w") as f:
            yaml.dump({"templates_dir": "custom_templates"}, f)
            
        config = load_config()
        assert config["templates_dir"] == "custom_templates"
        
        # Test CLI picks it up
        with patch("n8n_factory.cli.list_templates") as mock_list:
            with patch("sys.argv", ["n8n-factory", "list"]):
                main()
            # Default is "templates", config overrides? 
            # In cli.py: default_templates = defaults.get("templates_dir", "templates")
            # build_p.add_argument(..., default=default_templates)
            # So argparse default is updated.
            # We can't easily check default arg value via mock call if it wasn't passed explicit.
            # Wait, if I don't pass -t, it uses default.
            mock_list.assert_called_with("custom_templates", json_output=False)
    finally:
        os.chdir(cwd)

def test_load_config_missing(tmp_path):
    cwd = os.getcwd()
    os.chdir(tmp_path)
    if os.path.exists(".n8n-factory.yaml"): os.remove(".n8n-factory.yaml")
    try:
        config = load_config()
        assert config == {}
    finally:
        os.chdir(cwd)
