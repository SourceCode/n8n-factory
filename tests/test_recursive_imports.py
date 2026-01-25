import pytest
import yaml
from n8n_factory.utils import load_recipe

def test_recursive_imports(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    lib = root / "lib"
    lib.mkdir()
    
    # Create child recipe
    child_yaml = {
        "name": "Child",
        "steps": [{"id": "step1", "template": "set", "params": {"name": "foo", "value": "bar"}}]
    }
    (lib / "child.yaml").write_text(yaml.dump(child_yaml), encoding="utf-8")
    
    # Create parent recipe
    parent_yaml = {
        "name": "Parent",
        "imports": [{"path": "child.yaml", "namespace": "child"}],
        "steps": [{"id": "step2", "template": "set", "params": {"name": "baz", "value": "qux"}}]
    }
    (lib / "parent.yaml").write_text(yaml.dump(parent_yaml), encoding="utf-8")
    
    # Create main recipe
    main_yaml = {
        "name": "Recursive Test",
        "imports": [{"path": "lib/parent.yaml", "namespace": "parent"}],
        "steps": []
    }
    main_path = root / "main.yaml"
    main_path.write_text(yaml.dump(main_yaml), encoding="utf-8")
    
    recipe = load_recipe(str(main_path))
    
    ids = [s.id for s in recipe.steps]
    assert "parent_child_step1" in ids
    assert "parent_step2" in ids
    assert len(ids) == 2

def test_circular_import_detection(tmp_path):
    root = tmp_path / "cycle"
    root.mkdir()
    
    # A imports B, B imports A
    a_yaml = {"name": "A", "imports": ["b.yaml"], "steps": []}
    b_yaml = {"name": "B", "imports": ["a.yaml"], "steps": []}
    
    (root / "a.yaml").write_text(yaml.dump(a_yaml), encoding="utf-8")
    (root / "b.yaml").write_text(yaml.dump(b_yaml), encoding="utf-8")
    
    with pytest.raises(ValueError) as exc:
        load_recipe(str(root / "a.yaml"))
    
    assert "Circular import detected" in str(exc.value)