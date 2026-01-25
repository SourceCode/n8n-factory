from n8n_factory.optimizer import WorkflowOptimizer
from n8n_factory.models import Recipe, RecipeStep

def test_optimize_merge_sets():
    optimizer = WorkflowOptimizer()
    
    steps = [
        RecipeStep(id="s1", template="webhook"),
        RecipeStep(id="set1", template="set", params={"name": "a", "value": "1"}),
        RecipeStep(id="set2", template="set", params={"name": "b", "value": "2"}),
        RecipeStep(id="s2", template="webhook")
    ]
    recipe = Recipe(name="Opt", steps=steps)
    
    optimized = optimizer.optimize(recipe)
    
    assert len(optimized.steps) == 3
    assert optimized.steps[0].id == "s1"
    assert optimized.steps[1].template == "set_multi"
    assert len(optimized.steps[1].params["items"]) == 2
    assert optimized.steps[2].id == "s2"

def test_optimize_no_merge_needed():
    optimizer = WorkflowOptimizer()
    steps = [
        RecipeStep(id="set1", template="set", params={"name": "a", "value": "1"}),
        RecipeStep(id="webhook", template="webhook"),
        RecipeStep(id="set2", template="set", params={"name": "b", "value": "2"})
    ]
    recipe = Recipe(name="No Opt", steps=steps)
    
    optimized = optimizer.optimize(recipe)
    assert len(optimized.steps) == 3
    assert optimized.steps[0].template == "set"
    assert optimized.steps[2].template == "set"
