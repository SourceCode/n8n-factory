import pytest
from unittest.mock import patch, MagicMock
from n8n_factory.assembler import WorkflowAssembler
from n8n_factory.models import Recipe, RecipeStep, RetryConfig

@patch("n8n_factory.assembler.TemplateLoader")
def test_assembler_version_check(mock_loader, caplog):
    import logging
    caplog.set_level(logging.WARNING)
    
    with patch("n8n_factory.assembler.version", return_value="1.0.0"):
        asm = WorkflowAssembler()
        # Recipe requires 2.0.0
        recipe = Recipe(name="R", steps=[], n8n_factory_version="2.0.0")
        asm.assemble(recipe)
        assert "Recipe requires n8n-factory >= 2.0.0" in caplog.text

@patch("n8n_factory.assembler.TemplateLoader")
def test_assembler_duplicate_id(mock_loader):
    asm = WorkflowAssembler()
    mock_loader.return_value.render_template.return_value = {}
    
    recipe = Recipe(name="R", steps=[
        RecipeStep(id="s1", template="t"),
        RecipeStep(id="S1", template="t") # Case-insensitive duplicate
    ], strict=True)
    
    with pytest.raises(ValueError, match="Duplicate Node ID"):
        asm.assemble(recipe)

@patch("n8n_factory.assembler.TemplateLoader")
def test_assembler_auto_tag(mock_loader):
    asm = WorkflowAssembler()
    mock_loader.return_value.render_template.side_effect = [
        {"type": "n8n-nodes-base.awsS3"},
        {"type": "n8n-nodes-base.postgres"}
    ]
    
    recipe = Recipe(name="R", steps=[
        RecipeStep(id="s1", template="t"),
        RecipeStep(id="s2", template="t")
    ])
    
    wf = asm.assemble(recipe)
    # Tags are added to the recipe object
    tags = recipe.tags
    assert "aws" in tags
    assert "database" in tags

@patch("n8n_factory.assembler.TemplateLoader")
def test_assembler_step_options(mock_loader):
    asm = WorkflowAssembler()
    mock_loader.return_value.render_template.return_value = {}
    
    recipe = Recipe(name="R", steps=[
        RecipeStep(id="s1", template="t", 
                   notes="My Note", 
                   disabled=True, 
                   color="#ff0000",
                   retry=RetryConfig(maxTries=3, waitBetweenTries=1000))
    ])
    
    wf = asm.assemble(recipe)
    node = wf["nodes"][0]
    assert node["notes"] == "My Note"
    assert node["disabled"] is True
    assert node["retryOnFail"] is True
    assert node["maxTries"] == 3
    assert node["parameters"]["color"] == "#ff0000"

@patch("n8n_factory.assembler.TemplateLoader")
def test_assembler_meta_merge(mock_loader):
    asm = WorkflowAssembler()
    mock_loader.return_value.render_template.return_value = {}
    recipe = Recipe(name="R", steps=[], meta={"extra": "value"})
    wf = asm.assemble(recipe)
    assert "meta" not in wf
    assert "settings" in wf
    assert wf["settings"]["executionOrder"] == "v1"
