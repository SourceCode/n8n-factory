import json
from pydantic.json_schema import models_json_schema
from n8n_factory.models import Recipe

def generate_schema():
    schema = Recipe.model_json_schema()
    with open("recipe.schema.json", "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
    print("Generated recipe.schema.json")

if __name__ == "__main__":
    generate_schema()
