import os
import pytest
from unittest.mock import patch, MagicMock
from n8n_factory.assembler import WorkflowAssembler
from n8n_factory.models import Recipe, RecipeStep
from n8n_factory.loader import TemplateLoader

def test_assembler_settings_and_meta():
    # Mock loader to avoid file system dependency for this test
    with patch("n8n_factory.assembler.TemplateLoader") as MockLoader:
        asm = WorkflowAssembler()
        mock_loader = MockLoader.return_value
        mock_loader.render_template.return_value = {"type": "test"}
        
        recipe = Recipe(name="Test Settings", steps=[
            RecipeStep(id="s1", template="t")
        ])
        
        wf = asm.assemble(recipe)
        
        assert "meta" not in wf
        assert "settings" in wf
        assert wf["settings"]["executionOrder"] == "v1"

def test_assembler_loop_connections():
    with patch("n8n_factory.assembler.TemplateLoader") as MockLoader:
        asm = WorkflowAssembler()
        mock_loader = MockLoader.return_value
        mock_loader.render_template.return_value = {"type": "test"}
        
        # Create a loop: A -> B -> A
        # Normal connections_from would trigger cycle detection.
        # We use connections_loop for B -> A.
        
        recipe = Recipe(name="Loop Test", steps=[
            RecipeStep(id="A", template="t", connections_loop=["B"]),
            RecipeStep(id="B", template="t", connections_from=["A"])
        ])        
        wf = asm.assemble(recipe)
        
        connections = wf["connections"]
        
        # Check A -> B (main)
        assert "B" in connections
        assert any(c[0]["node"] == "A" for c in connections["B"]["main"])
        
        # Check B -> A (loop)
        # connections_loop=["B"] on A means A has incoming from B.
        # So "A" in connections should have B.
        assert "A" in connections
        assert any(c[0]["node"] == "B" for c in connections["A"]["main"])

def test_template_split_in_batches_default():
    templates_dir = os.path.abspath("templates")
    loader = TemplateLoader(templates_dir)
    # This relies on the actual template file being present
    try:
        rendered = loader.render_template("split_in_batches", {})
        # batchSize defaults to 1
        assert rendered["parameters"]["batchSize"] == 1
    except Exception as e:
        pytest.fail(f"Failed to render split_in_batches: {e}")

def test_template_ollama_http_generate():
    templates_dir = os.path.abspath("templates")
    loader = TemplateLoader(templates_dir)
    try:
        params = {
            "prompt": "Hello",
            "model": "gpt4",
            "temperature": 0.5
        }
        rendered = loader.render_template("ollama_http_generate", params)
        
        assert rendered["type"] == "n8n-nodes-base.httpRequest"
        assert rendered["parameters"]["options"]["timeout"] == 600000
        
        # Check JSON Body
        json_body = rendered["parameters"]["jsonBody"]
        import json
        body = json.loads(json_body)
        
        assert body["model"] == "gpt4"
        assert body["prompt"] == "Hello"
        assert body["stream"] is False
        assert body["options"]["temperature"] == 0.5
        
    except Exception as e:
        pytest.fail(f"Failed to render ollama_http_generate: {e}")