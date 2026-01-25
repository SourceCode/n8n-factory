import pytest
import json
import logging
from unittest.mock import patch, mock_open
from n8n_factory.simulator import WorkflowSimulator
from n8n_factory.models import Recipe, RecipeStep

def test_simulator_file_mock(tmp_path, caplog):
    caplog.set_level(logging.INFO)
    sim = WorkflowSimulator()
    
    # Valid file
    data = tmp_path / "data.json"
    data.write_text('{"foo": "bar"}', encoding="utf-8")
    
    # Needs escaping for Windows paths in JSON string if not careful, but f-string handles it?
    # RecipeStep(mock=...) handles objects. But if I pass "file:...", it's a string.
    # Path object str() might have backslashes.
    # Let's use as_posix() to be safe.
    path_str = data.as_posix()
    
    steps = [RecipeStep(id="s1", template="webhook", mock=f"file:{path_str}")]
    recipe = Recipe(name="File Mock", steps=steps)
    
    res = sim.simulate(recipe)
    assert res[0]["output"][0]["json"]["foo"] == "bar"
    
    # Invalid file
    steps_bad = [RecipeStep(id="s2", template="webhook", mock="file:missing.json")]
    recipe_bad = Recipe(name="Bad File", steps=steps_bad)
    
    sim.simulate(recipe_bad)
    assert "Mock data file not found" in caplog.text

def test_simulator_auto_mock_if(caplog):
    caplog.set_level(logging.INFO)
    sim = WorkflowSimulator()
    
    steps = [
        RecipeStep(id="s1", template="if", params={"left": "a", "right": "a", "operator": "equal"}),
        RecipeStep(id="s2", template="if", params={"left": "a", "right": "b", "operator": "notEqual"}),
        RecipeStep(id="s3", template="if", params={"left": "a", "right": "b", "operator": "equal"})
    ]
    recipe = Recipe(name="Auto Mock", steps=steps)
    
    sim.simulate(recipe)
    
    assert "Condition: 'a' equal 'a' -> True" in caplog.text
    assert "Condition: 'a' notEqual 'b' -> True" in caplog.text
    assert "Condition: 'a' equal 'b' -> False" in caplog.text

def test_simulator_expression_resolution():
    sim = WorkflowSimulator()
    ctx = {"json": {"a": 1, "b": {"c": 2}}}
    
    # Simple
    assert sim._resolve_expressions("{{ $json.a }}", ctx) == "1"
    
    # Nested dict
    res_dict = sim._resolve_expressions({"val": "{{ $json.a }}"}, ctx)
    assert res_dict["val"] == "1"
    
    # List
    res_list = sim._resolve_expressions(["{{ $json.a }}"], ctx)
    assert res_list[0] == "1"
    
    # Missing
    assert sim._resolve_expressions("{{ $json.missing }}", ctx) == "{{ $json.missing }}" 

def test_simulator_expression_resolution_str_match():
    # Regex coverage
    sim = WorkflowSimulator()
    ctx = {"json": {"x": "y", "b": {"c": 2}}}
    # match spaces
    assert sim._resolve_expressions("{{ $json.x }}", ctx) == "y"
    # match no spaces
    assert sim._resolve_expressions("{{$json.x}}", ctx) == "y" 
    
    # Nested keys
    assert sim._resolve_expressions("{{ $json.b }}", ctx) == "{'c': 2}"