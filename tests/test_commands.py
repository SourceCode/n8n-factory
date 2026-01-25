import pytest
import sys
import json
import os
from unittest.mock import patch, MagicMock
from n8n_factory.cli import main

@pytest.fixture
def mock_recipe(tmp_path):
    p = tmp_path / "recipe.yaml"
    p.write_text('name: "Test"\ndescription: "A test recipe"\nsteps: []', encoding="utf-8")
    return str(p)

def run_cli(args):
    with patch.object(sys, 'argv', ["n8n-factory"] + args):
        try:
            main()
        except SystemExit as e:
            return e.code
    return 0

def test_command_list(temp_templates_dir, capsys):
    run_cli(["list", "-t", temp_templates_dir])
    assert "Available Templates" in capsys.readouterr().out
    
    run_cli(["list", "-t", temp_templates_dir, "--json"])
    out = capsys.readouterr().out
    assert "webhook" in out
    assert "[" in out 

def test_command_search(temp_templates_dir, capsys):
    run_cli(["search", "webhook", "-t", temp_templates_dir])
    assert "Search Results" in capsys.readouterr().out

def test_command_info(mock_recipe, capsys):
    run_cli(["info", mock_recipe])
    assert "Recipe Info" in capsys.readouterr().out

def test_command_export(mock_recipe, capsys):
    run_cli(["export", mock_recipe])
    assert "name: Test" in capsys.readouterr().out

def test_command_template_new(tmp_path, capsys):
    with patch("rich.prompt.Prompt.ask", side_effect=["my_tmpl", "type", "p1", "def", ""]):
        with patch("rich.prompt.Confirm.ask", side_effect=[True, False]):
            run_cli(["template", "new", "--output-dir", str(tmp_path)])
    
    assert (tmp_path / "my_tmpl.json").exists()

def test_command_init(tmp_path):
    with patch("rich.prompt.Prompt.ask", side_effect=["My Flow", "Desc", "path", "step1", "code", ""]):
        with patch("rich.prompt.Confirm.ask", side_effect=[True, True, False]):
            with patch("os.makedirs"): 
                with patch("builtins.open", create=True) as mock_open:
                     run_cli(["init"])

def test_command_diff(mock_recipe, tmp_path):
    run_cli(["diff", mock_recipe, mock_recipe]) 
    
def test_command_validate(mock_recipe, temp_templates_dir, capsys):
    run_cli(["validate", mock_recipe, "-t", temp_templates_dir])
    assert "Validation Passed" in capsys.readouterr().out

def test_command_lint(mock_recipe, temp_templates_dir, capsys):
    run_cli(["lint", mock_recipe, "-t", temp_templates_dir])
    assert "Lint Passed" in capsys.readouterr().out

def test_command_stats(mock_recipe, capsys):
    run_cli(["stats", mock_recipe])
    assert "Statistics" in capsys.readouterr().out

def test_command_doctor(capsys):
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        with patch.dict(os.environ, {"N8N_URL": "http://x", "N8N_API_KEY": "x"}):
            run_cli(["doctor"])
    assert "n8n Factory Doctor" in capsys.readouterr().out

def test_command_clean(tmp_path, capsys):
    (tmp_path / "junk.json").touch()
    with patch("os.getcwd", return_value=str(tmp_path)):
        with patch("glob.glob", return_value=["junk.json"]):
            with patch("os.remove") as mock_rm:
                run_cli(["clean"])
                mock_rm.assert_called_with("junk.json")

def test_command_tree(mock_recipe, capsys):
    run_cli(["tree", mock_recipe])
    assert "Test" in capsys.readouterr().out

def test_command_benchmark(temp_templates_dir, capsys):
    run_cli(["benchmark", "--size", "10"]) 
    assert "Build Time" in capsys.readouterr().out

def test_command_bundle(mock_recipe, tmp_path):
    out = tmp_path / "bundle.zip"
    run_cli(["bundle", mock_recipe, "--output", str(out)])
    assert out.exists()

def test_command_examples(capsys):
    run_cli(["examples"])
    assert "Examples" in capsys.readouterr().out

def test_command_profile(tmp_path, capsys):
    (tmp_path / ".env.dev").touch()
    with patch("os.path.exists", return_value=True): 
        with patch("shutil.copy") as mock_cp:
            run_cli(["profile", "dev"])
            mock_cp.assert_called()

def test_command_login(capsys):
    with patch("rich.prompt.Prompt.ask", side_effect=["url", "key"]):
        with patch("builtins.open", create=True):
             run_cli(["login"])