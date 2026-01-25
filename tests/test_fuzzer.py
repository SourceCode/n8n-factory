import pytest
import random
import string
import json
from pydantic import ValidationError
from n8n_factory.models import Recipe

def random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_random_recipe_dict():
    steps = []
    for i in range(random.randint(1, 5)):
        steps.append({
            "id": random_string(),
            "template": random_string(),
            "params": {random_string(): random_string()}
        })
    
    return {
        "name": random_string(),
        "steps": steps
    }

def test_fuzzer_valid_recipes():
    """Generates random valid-ish dicts and checks if Pydantic accepts them (or fails gracefully)."""
    for _ in range(50):
        data = generate_random_recipe_dict()
        try:
            recipe = Recipe(**data)
            assert recipe.name == data["name"]
            assert len(recipe.steps) == len(data["steps"])
        except ValidationError:
            # Should not happen if generator follows schema, but if it does, it's a finding?
            # Actually we just want to ensure it doesn't crash unexpectedly.
            # If we generate intentionally valid structure, it should pass.
            pytest.fail(f"Valid schema failed validation: {data}")

def test_fuzzer_invalid_ids():
    """Generates recipe with duplicate IDs."""
    data = generate_random_recipe_dict()
    if len(data["steps"]) > 0:
        # Duplicate ID
        data["steps"].append(data["steps"][0].copy())
        
        with pytest.raises(ValueError) as exc:
            Recipe(**data)
        assert "Duplicate step IDs" in str(exc.value)
