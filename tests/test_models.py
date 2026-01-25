from n8n_factory.models import Recipe, RecipeStep
from pydantic import ValidationError
import pytest

def test_recipe_step_creation():
    step = RecipeStep(id="test", template="webhook", params={"p": 1})
    assert step.id == "test"
    assert step.template == "webhook"
    assert step.params["p"] == 1
    assert step.debug is False
    assert step.mock is None

def test_recipe_step_mock_and_debug():
    step = RecipeStep(id="test", template="webhook", mock={"a": 1}, debug=True)
    assert step.mock == {"a": 1}
    assert step.debug is True

def test_recipe_creation():
    step1 = RecipeStep(id="1", template="t1")
    recipe = Recipe(name="My Recipe", steps=[step1])
    assert recipe.name == "My Recipe"
    assert len(recipe.steps) == 1

def test_recipe_validation_missing_fields():
    with pytest.raises(ValidationError):
        Recipe(name="Incomplete") # Missing steps

    with pytest.raises(ValidationError):
        RecipeStep(id="no-template") # Missing template
