import pytest
from unittest.mock import patch, MagicMock
from n8n_factory.simulator import WorkflowSimulator
from n8n_factory.models import Recipe, RecipeStep
from n8n_factory.commands.watch import watch_recipe
from n8n_factory.commands.serve import serve_command

def test_simulator_step_mode(caplog):
    simulator = WorkflowSimulator()
    steps = [RecipeStep(id="s1", template="webhook")]
    recipe = Recipe(name="Step Sim", steps=steps)
    
    with patch("builtins.input", side_effect=["", ""]): # Press enter
        simulator.simulate(recipe, step_mode=True)
    
    assert "Step 1: s1" in caplog.text

def test_simulator_breakpoint_print(capsys):
    simulator = WorkflowSimulator()
    steps = [RecipeStep(id="s1", template="webhook", breakpoint=True)]
    recipe = Recipe(name="Break Sim", steps=steps)
    
    with patch("builtins.input", side_effect=[""]):
        simulator.simulate(recipe, interactive=True)
    
    assert "BREAKPOINT" in capsys.readouterr().out

def test_command_watch(tmp_path):
    (tmp_path / "recipe.yaml").touch()
    with patch("n8n_factory.commands.watch.Observer") as MockObserver:
        obs_instance = MockObserver.return_value
        with patch("time.sleep", side_effect=KeyboardInterrupt):
            watch_recipe(str(tmp_path / "recipe.yaml"), "templates")
        
        obs_instance.start.assert_called()
        obs_instance.stop.assert_called()

def test_command_serve(tmp_path):
    (tmp_path / "recipe.yaml").write_text('name: "S"\nsteps: []', encoding="utf-8")
    with patch("socketserver.TCPServer") as MockServer:
        server_instance = MockServer.return_value
        # Configure context manager to return the instance itself
        server_instance.__enter__.return_value = server_instance
        
        server_instance.serve_forever.side_effect = KeyboardInterrupt
        
        with patch("webbrowser.open"):
            serve_command(str(tmp_path / "recipe.yaml"))
            
        server_instance.serve_forever.assert_called()
