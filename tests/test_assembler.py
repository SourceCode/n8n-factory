from n8n_factory.assembler import WorkflowAssembler
from n8n_factory.models import Recipe, RecipeStep, RetryConfig
import pytest

def test_assemble_simple_workflow(temp_templates_dir):
    assembler = WorkflowAssembler(templates_dir=temp_templates_dir)
    
    # Corrected params: 'method' instead of 'httpMethod' to match template variable
    steps = [
        RecipeStep(id="step1", template="webhook", params={"path": "a", "method": "GET"}),
        RecipeStep(id="step2", template="webhook", params={"path": "b", "method": "POST"})
    ]
    recipe = Recipe(name="Simple Flow", steps=steps)
    
    workflow = assembler.assemble(recipe)
    
    assert workflow["name"] == "Simple Flow"
    assert len(workflow["nodes"]) == 2
    
    connections = workflow["connections"]
    assert "step1" in connections

def test_assemble_with_debug(temp_templates_dir):
    assembler = WorkflowAssembler(templates_dir=temp_templates_dir)
    
    steps = [
        RecipeStep(id="step1", template="webhook", params={"path": "a", "method": "GET"}, debug=True),
        RecipeStep(id="step2", template="webhook", params={"path": "b", "method": "POST"})
    ]
    recipe = Recipe(name="Debug Flow", steps=steps)
    
    workflow = assembler.assemble(recipe)
    assert len(workflow["nodes"]) == 3

def test_assemble_advanced_fields(temp_templates_dir):
    assembler = WorkflowAssembler(templates_dir=temp_templates_dir)
    steps = [
        RecipeStep(
            id="s1", 
            template="webhook", 
            params={"path": "a", "method": "GET"},
            notes="My Note",
            color="#ff0000",
            disabled=True,
            retry=RetryConfig(maxTries=3, waitBetweenTries=500)
        )
    ]
    recipe = Recipe(name="Adv", steps=steps)
    wf = assembler.assemble(recipe)
    node = wf["nodes"][0]
    
    assert node["notesInFlow"] is True
    assert node["notes"] == "My Note"
    assert node["disabled"] is True
    assert node["retryOnFail"] is True
    assert node["maxTries"] == 3
    assert node["parameters"]["color"] == "#ff0000"

def test_assembler_secret_scan_strict(temp_templates_dir):
    assembler = WorkflowAssembler(templates_dir=temp_templates_dir)
    steps = [
        RecipeStep(id="s1", template="webhook", params={"path": "a", "method": "GET", "api_key": "12345678"})
    ]
    recipe = Recipe(name="Secret", steps=steps, strict=True)
    
    with pytest.raises(ValueError) as exc:
        assembler.assemble(recipe)
    assert "Security Warning" in str(exc.value)
