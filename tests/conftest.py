import pytest
import os
import json
import shutil

@pytest.fixture
def temp_templates_dir(tmp_path):
    """Creates a temporary directory with some mock templates."""
    d = tmp_path / "templates"
    d.mkdir()
    
    # Create a basic template (Updated to match real webhook.json)
    webhook_template = {
        "parameters": {
            "path": "{{ path }}",
            "httpMethod": "{{ method }}"
        },
        "type": "n8n-nodes-base.webhook",
        "typeVersion": 1,
        "position": [0, 0]
    }
    
    with open(d / "webhook.json", "w") as f:
        json.dump(webhook_template, f)

    # Create a debug template (needed for assembler tests with debug=True)
    debug_template = {
        "parameters": {
            "jsCode": "console.log('DEBUG:', items); return items;"
        },
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [0, 0]
    }
    with open(d / "debug_logger.json", "w") as f:
        json.dump(debug_template, f)

    # Create set and set_multi templates for optimizer
    set_template = {
        "parameters": {
            "assignments": {
                "assignments": [
                    {
                        "name": "{{ name }}",
                        "value": "{{ value }}"
                    }
                ]
            }
        },
        "type": "n8n-nodes-base.set"
    }
    with open(d / "set.json", "w") as f:
        json.dump(set_template, f)

    return str(d)