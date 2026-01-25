import pytest
import os
import json
from n8n_factory.loader import TemplateLoader

def test_load_template_success(temp_templates_dir):
    loader = TemplateLoader(templates_dir=temp_templates_dir)
    content = loader.load_template_raw("webhook")
    assert "n8n-nodes-base.webhook" in content

def test_load_template_not_found(temp_templates_dir):
    loader = TemplateLoader(templates_dir=temp_templates_dir)
    with pytest.raises(FileNotFoundError):
        loader.load_template_raw("non_existent_template")

def test_render_template_success(temp_templates_dir):
    loader = TemplateLoader(templates_dir=temp_templates_dir)
    params = {"path": "my-hook", "method": "POST"}
    rendered = loader.render_template("webhook", params)
    
    assert rendered["parameters"]["path"] == "my-hook"
    assert rendered["parameters"]["httpMethod"] == "POST"
    assert rendered["type"] == "n8n-nodes-base.webhook"

def test_render_template_invalid_json(temp_templates_dir, tmp_path):
    # Create a broken template
    d = tmp_path / "broken_templates"
    d.mkdir()
    with open(d / "bad.json", "w") as f:
        f.write("{ invalid json {{ val }}")
    
    loader = TemplateLoader(templates_dir=str(d))
    
    with pytest.raises(ValueError) as excinfo:
        loader.render_template("bad", {"val": "1"})
    assert "Failed to parse rendered JSON" in str(excinfo.value)

def test_template_inheritance(tmp_path):
    d = tmp_path / "templates"
    d.mkdir()
    
    # Base
    base = {
        "parameters": {"a": "{{ a }}", "b": "base"},
        "type": "base",
        "_meta": {"required_params": ["a"]}
    }
    (d / "base.json").write_text(json.dumps(base), encoding="utf-8")
    
    # Child
    child = {
        "_meta": {"extends": "base"},
        "parameters": {"b": "override", "c": "child"}
    }
    (d / "child.json").write_text(json.dumps(child), encoding="utf-8")
    
    loader = TemplateLoader(templates_dir=str(d))
    
    # Render Child
    rendered = loader.render_template("child", {"a": "val"})
    
    assert rendered["type"] == "base" # Inherited
    assert rendered["parameters"]["a"] == "val" # Inherited param usage
    assert rendered["parameters"]["b"] == "override" # Overridden
    assert rendered["parameters"]["c"] == "child" # Added

def test_template_validation(tmp_path, caplog):
    d = tmp_path / "templates"
    d.mkdir()
    
    tmpl = {
        "_meta": {
            "param_types": {"num": "number", "bool": "boolean"},
            "deprecated": True
        },
        "parameters": {"num": "{{ num }}", "bool": "{{ bool }}"},
        "type": "test"
    }
    (d / "val.json").write_text(json.dumps(tmpl), encoding="utf-8")
    
    loader = TemplateLoader(templates_dir=str(d))
    
    # Valid
    loader.render_template("val", {"num": 123, "bool": True})
    
    # Invalid types
    loader.render_template("val", {"num": "string", "bool": 1})
    
    assert "expected number" in caplog.text
    assert "expected boolean" in caplog.text
    assert "is deprecated" in caplog.text