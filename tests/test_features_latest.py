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
        
        recipe = Recipe(name="Loop Test", steps=[
            RecipeStep(id="A", template="t", connections_loop=["B"]),
            RecipeStep(id="B", template="t", connections_from=["A"])
        ])        
        wf = asm.assemble(recipe)
        
        connections = wf["connections"]
        
        assert "B" in connections
        assert any(c[0]["node"] == "A" for c in connections["B"]["main"])
        
        assert "A" in connections
        assert any(c[0]["node"] == "B" for c in connections["A"]["main"])

def test_template_split_in_batches_default():
    templates_dir = os.path.abspath("templates")
    loader = TemplateLoader(templates_dir)
    try:
        rendered = loader.render_template("split_in_batches", {})
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
        
        # Check Retries
        assert rendered["retryOnFail"] is True
        assert rendered["maxTries"] == 3
        assert rendered["waitBetweenTries"] == 5000
        
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

def test_template_progress_marker():
    templates_dir = os.path.abspath("templates")
    loader = TemplateLoader(templates_dir)
    try:
        params = {"run_id": "r1", "item_id": "i1"}
        rendered = loader.render_template("progress_marker", params)
        assert rendered["type"] == "n8n-nodes-base.redis"
        assert rendered["parameters"]["key"] == "progress:r1:i1"
        assert rendered["parameters"]["options"]["ttl"] == 3600
    except Exception as e:
        pytest.fail(f"Failed to render progress_marker: {e}")

def test_template_safe_slugify():
    templates_dir = os.path.abspath("templates")
    loader = TemplateLoader(templates_dir)
    try:
        rendered = loader.render_template("safe_slugify", {"field": "topic"})
        assert rendered["type"] == "n8n-nodes-base.code"
        assert "replace" in rendered["parameters"]["code"]
        assert "topic" in rendered["parameters"]["code"]
    except Exception as e:
        pytest.fail(f"Failed to render safe_slugify: {e}")
