import pytest
from n8n_factory.graph import DependencyGraph
from n8n_factory.models import RecipeStep

def test_graph_cycles():
    steps = [
        RecipeStep(id="A", template="t", connections_from=["B"]),
        RecipeStep(id="B", template="t", connections_from=["A"])
    ]
    g = DependencyGraph(steps)
    with pytest.raises(ValueError):
        g.detect_cycles()

def test_graph_orphans():
    steps = [
        RecipeStep(id="A", template="webhook"),
        RecipeStep(id="B", template="t", connections_from=["A"]),
        # Break auto-wiring by explicit empty list
        RecipeStep(id="C", template="t", connections_from=[]) 
    ]
    g = DependencyGraph(steps)
    g.detect_orphans(strict=False)
    with pytest.raises(ValueError):
        g.detect_orphans(strict=True)

def test_graph_downstream():
    steps = [
        RecipeStep(id="A", template="t"),
        RecipeStep(id="B", template="t", connections_from=["A"]),
        RecipeStep(id="C", template="t", connections_from=["B"])
    ]
    g = DependencyGraph(steps)
    ds = g.get_downstream_nodes("A")
    assert "A" in ds
    assert "B" in ds
    assert "C" in ds
    assert len(ds) == 3
