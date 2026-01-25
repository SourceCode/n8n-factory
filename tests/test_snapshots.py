import json
import pytest
from n8n_factory.assembler import WorkflowAssembler
from n8n_factory.models import Recipe, RecipeStep

def test_template_snapshots(temp_templates_dir):
    """
    Verifies that core templates generate expected JSON structure.
    """
    assembler = WorkflowAssembler(templates_dir="templates")
    
    # Snapshot 1: Webhook
    steps = [RecipeStep(id="hook", template="webhook", params={"path": "test", "method": "GET", "uuid": "u1"})]
    wf = assembler.assemble(Recipe(name="Snapshot", steps=steps))
    node = wf["nodes"][0]
    assert node["type"] == "n8n-nodes-base.webhook"
    
    # Snapshot 2: AWS S3 (Existing)
    steps = [RecipeStep(id="s3", template="s3", params={"bucketName": "my-bucket", "fileKey": "key"})]
    wf = assembler.assemble(Recipe(name="AWS", steps=steps))
    node = wf["nodes"][0]
    assert node["type"] == "n8n-nodes-base.awsS3"
    
    # Snapshot 3: Ollama Chat (New)
    steps = [RecipeStep(id="ai", template="ollama_chat", params={"prompt": "hello", "model": "llama3"})]
    wf = assembler.assemble(Recipe(name="AI", steps=steps))
    node = wf["nodes"][0]
    assert node["type"] == "n8n-nodes-base.ollama"
    assert node["parameters"]["resource"] == "chat"
    assert node["parameters"]["model"] == "llama3"

    # Snapshot 4: Vector Store (New)
    steps = [RecipeStep(id="vec", template="vector_store_upsert", params={"collection": "my_docs"})]
    wf = assembler.assemble(Recipe(name="RAG", steps=steps))
    node = wf["nodes"][0]
    assert node["type"] == "n8n-nodes-base.qdrant"
    assert node["parameters"]["collection"] == "my_docs"
