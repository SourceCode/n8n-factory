from n8n_factory.assembler import WorkflowAssembler
from n8n_factory.models import Recipe, RecipeStep
import pytest

def test_assemble_explicit_wiring(temp_templates_dir):
    assembler = WorkflowAssembler(templates_dir=temp_templates_dir)
    
    # Define steps out of order or with explicit override
    steps = [
        RecipeStep(id="start", template="webhook", params={"path": "p", "method": "m"}),
        RecipeStep(id="branch_a", template="set", params={"name":"a","value":"1"}, connections_from=["start"]),
        RecipeStep(id="branch_b", template="set", params={"name":"b","value":"2"}, connections_from=["start"]),
        RecipeStep(id="merge", template="set", params={"name":"c","value":"3"}, connections_from=["branch_a", "branch_b"])
    ]
    recipe = Recipe(name="Explicit Flow", steps=steps)
    
    workflow = assembler.assemble(recipe)
    conns = workflow["connections"]
    
    # Start -> Branch A
    assert "start" in conns
    assert any(c["node"] == "branch_a" for c in conns["start"]["main"][0])
    
    # Start -> Branch B (start connects to multiple)
    assert any(c["node"] == "branch_b" for c in conns["start"]["main"][0])
    
    # Branch A -> Merge
    assert conns["branch_a"]["main"][0][0]["node"] == "merge"
    
    # Branch B -> Merge
    assert conns["branch_b"]["main"][0][0]["node"] == "merge"

def test_assemble_explicit_missing_ref(temp_templates_dir):
    assembler = WorkflowAssembler(templates_dir=temp_templates_dir)
    steps = [
        RecipeStep(id="s1", template="webhook", params={"path": "p", "method": "m"}, connections_from=["non_existent"])
    ]
    recipe = Recipe(name="Bad Flow", steps=steps)
    
    with pytest.raises(ValueError) as exc:
        assembler.assemble(recipe)
    # Update expected message to match new implementation
    assert "unknown step" in str(exc.value)
