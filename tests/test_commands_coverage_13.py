import pytest
import os
import yaml
from unittest.mock import MagicMock, patch
from n8n_factory.cli import main
from n8n_factory.utils import load_recipe

# --- CLI Exception Console ---
def test_cli_exception_console_raise(capsys):
    with patch("n8n_factory.cli.list_templates", side_effect=Exception("Console Crash")):
        with patch("sys.argv", ["n8n-factory", "list"]):
            with pytest.raises(Exception, match="Console Crash"):
                main()

# --- Utils Import Connections ---
def test_import_with_connections(tmp_path):
    # base.yaml imports sub.yaml
    # sub.yaml has step s1 connecting to s2
    # load_recipe should rename nodes and connections
    
    sub = tmp_path / "sub.yaml"
    sub.write_text("""
name: Sub
steps:
  - id: s1
    template: t
    connections_from: 
      - s2
  - id: s2
    template: t
""", encoding="utf-8")
    
    base = tmp_path / "base.yaml"
    base.write_text("""
name: Base
imports:
  - path: sub.yaml
    namespace: nested
steps: []
""", encoding="utf-8")
    
    recipe = load_recipe(str(base))
    # Check steps
    s1 = next(s for s in recipe.steps if "s1" in s.id)
    assert s1.id == "nested_s1"
    assert s1.connections_from == ["nested_s2"]
