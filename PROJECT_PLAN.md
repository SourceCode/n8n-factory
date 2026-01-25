# n8n-factory Project Plan

## Objective
Create a Python-based tool to assemble n8n workflows from reusable, optimized templates. The tool is designed to be "AI-First," meaning its primary user is intended to be an AI agent crafting workflows.

## Architecture
- **Language:** Python 3.10+
- **Input:** "Recipes" (YAML/JSON) defining the workflow logic.
- **Assets:** "Templates" (JSON) representing partial n8n node configurations.
- **Output:** Valid `n8n` workflow JSON files importable into n8n.

## Phases

### Phase 1: Foundation & Configuration
**Goal:** Set up the project structure and define the schema for interaction.
- [ ] Initialize Python project with `pyproject.toml`.
- [ ] Create directory structure: `src/`, `templates/`, `recipes/`, `tests/`.
- [ ] Create `AGENTS.md`: The definitive guide for AI on how to utilize this factory.
- [ ] Define `Recipe` schema (Pydantic model) for strict typing.

### Phase 2: Core Logic (The Factory)
**Goal:** Implement the logic to read templates and assemble workflows.
- [ ] **TemplateLoader:** Module to scan and load JSON templates from the `templates/` directory.
- [ ] **NodeConfigurator:** Module to inject variables into templates (using Jinja2 or standard format strings) to produce concrete nodes.
- [ ] **WorkflowAssembler:** The core engine.
    -   Takes a list of steps from a Recipe.
    -   Instantiates nodes.
    -   **Auto-Wiring:** Automatically generates the `connections` object (linking Node A -> Node B) unless overridden.
    -   Handles n8n specific structures like `meta` and `settings`.
- [ ] **CLI Entrypoint:** A `main.py` using `argparse` or `click` to run the build process.

### Phase 3: Template Library
**Goal:** Seed the factory with high-quality, reusable node templates.
- [ ] **Webhook Template:** Standard entry point.
- [ ] **Code Node Template:** Python/JS execution blocks.
- [ ] **HTTP Request Template:** For API interactions.
- [ ] **AI Agent Template:** Placeholder for AI nodes (since this is an AI factory).
- [ ] **Switch/If Template:** Branching logic.

### Phase 4: Testing & Verification
**Goal:** Ensure generated workflows are valid JSON and importable.
- [x] Unit tests for `WorkflowAssembler`.
- [x] Integration test: Build a complex workflow from a sample recipe.
- [x] JSON Schema validation against n8n's expected format (best effort).
- [x] **Achieve >90% Test Coverage** (Current: 94%)

### Phase 5: Simulation Engine
**Goal:** Simulate workflow execution locally using mock data to verify logic.
- [ ] **Mock Schema:** Extend `Recipe` to support defining mock inputs/outputs for steps.
- [ ] **Simulator:** Engine to iterate through steps, injecting mock data instead of executing real nodes.
- [ ] **CLI Command:** `simulate` command to run a recipe with mocks and report results.

### Phase 6: Optimizer
**Goal:** Analyze and refine recipes to reduce steps and improve efficiency.
- [ ] **Optimizer Engine:** Static analysis of the `Recipe` model.
- [ ] **Optimization Rules:**
    -   **Merge Set Nodes:** Combine adjacent `set` nodes into a single node.
    -   **Prune Unused:** Remove steps that don't contribute to the final output (experimental).
- [ ] **CLI Command:** `optimize` command to auto-refine a recipe file.

### Phase 7: Debugging & Instrumentation
**Goal:** Inject debugging and data capture capabilities into workflows.
- [ ] **Debug Flag:** Add `debug: true` option to `RecipeStep`.
- [ ] **Debug Template:** Create a `debug_logger` node that logs `items` to the n8n console.
- [ ] **Assembler Logic:** Automatically inject and wire debug nodes during build if requested.

## AI Workflow Strategy (for AGENTS.md)
1.  **Discovery:** AI Agent checks `templates/` to see available tools.
2.  **Planning:** AI Agent constructs a `recipe.yaml` mapping a logical flow to specific templates.
3.  **Execution:** AI Agent calls `python -m n8n_factory build recipe.yaml`.
4.  **Refinement:** AI Agent analyzes the output or errors and iterates on the template or recipe.
