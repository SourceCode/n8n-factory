from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, field_validator

class RetryConfig(BaseModel):
    maxTries: int = 1
    waitBetweenTries: int = 1000 # ms

class Connection(BaseModel):
    node: str
    type: str = "main"
    index: int = 0

class RecipeStep(BaseModel):
    id: str
    template: str
    params: Dict[str, Any] = {}
    mock: Optional[Any] = None
    mock_error: Optional[str] = None 
    mock_latency: Optional[int] = None
    breakpoint: bool = False
    debug: bool = False
    description: Optional[str] = None
    # Improvement #1: Complex Connections
    connections_from: Optional[List[Union[str, Connection]]] = None
    connections_loop: Optional[List[Union[str, Connection]]] = None
    position: Optional[List[int]] = None
    color: Optional[str] = None
    notes: Optional[str] = None
    disabled: bool = False
    retry: Optional[RetryConfig] = None

class ImportItem(BaseModel):
    path: str
    namespace: Optional[str] = None

class Recipe(BaseModel):
    name: str
    description: Optional[str] = None
    tags: List[str] = []
    globals: Dict[str, Any] = {}
    imports: List[Union[str, ImportItem]] = []
    strict: bool = False
    # Improvement #2: Workflow Meta
    meta: Dict[str, Any] = {}
    # Improvement #3: Version Pinning
    n8n_factory_version: Optional[str] = None
    assertions: List[str] = []
    steps: List[RecipeStep]

    @field_validator('steps')
    @classmethod
    def check_unique_ids(cls, v: List[RecipeStep]) -> List[RecipeStep]:
        ids = [step.id for step in v]
        if len(ids) != len(set(ids)):
            from collections import Counter
            duplicates = [item for item, count in Counter(ids).items() if count > 1]
            raise ValueError(f"Duplicate step IDs found: {duplicates}")
        return v