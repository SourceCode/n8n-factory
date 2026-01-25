import pytest
import os
import json
from n8n_factory.loader import TemplateLoader

def test_read_file_helper(tmp_path):
    # Create a dummy file
    f = tmp_path / "data.txt"
    f.write_text("hello world", encoding="utf-8")
    
    # Path needs to be escaped for JSON string if windows backslashes
    # as_posix() handles this
    path_str = f.as_posix()
    
    # Create a template that uses read_file
    t = tmp_path / "templates"
    t.mkdir()
    
    # Using Jinja syntax: {{ read_file('path') }}
    # Escaping logic for the test string creation
    template_content = {
        "content": "{{ read_file('" + path_str + "') }}"
    }
    
    (t / "reader.json").write_text(json.dumps(template_content), encoding="utf-8")
    
    loader = TemplateLoader(templates_dir=str(t))
    rendered = loader.render_template("reader", {})
    
    assert rendered["content"] == "hello world"

def test_env_var_resolution(monkeypatch, tmp_path):
    monkeypatch.setenv("MY_VAR", "secret_value")
    
    t = tmp_path / "templates"
    t.mkdir()
    (t / "env.json").write_text('{"val": "${MY_VAR}"}', encoding="utf-8")
    
    loader = TemplateLoader(templates_dir=str(t))
    rendered = loader.render_template("env", {})
    
    assert rendered["val"] == "secret_value"