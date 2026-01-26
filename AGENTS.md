# AI Agent Guide for n8n-factory

This document is the definitive guide for AI agents using `n8n-factory`.

## Core Concept
Instead of writing raw, monolithic JSON for n8n, you construct **Recipes** (YAML) that reference **Templates**. The factory then assembles these into valid `workflow.json` files. You can also manage, optimize, and debug running workflows.

## Workflow Generation Process

1.  **Analyze Request:** Understand the user's goal.
2.  **Explore Templates:** List files in `templates/` using `n8n-factory list --json`.
3.  **Create Recipe:** Write a YAML file (e.g., `recipes/my_workflow.yaml`).
4.  **Build:** Run `n8n-factory build recipes/my_workflow.yaml`.
5.  **Deliver:** The output is a JSON file ready for n8n import.

## CLI Usage (JSON Mode)
**Always** use the `--json` flag where available for machine-readable output.

### 1. Discovery
```bash
# List all available templates
n8n-factory list --json

# Search for a specific template
n8n-factory search "webhook" --json

# Inspect a template's parameters
n8n-factory inspect webhook --json
```

### 2. Runtime Operations (Docker/DB)
Use the `ops` command to interact with the environment.
```bash
# Get n8n logs
n8n-factory ops logs --service n8n --tail 50 --json

# Query the database
n8n-factory ops db --query "SELECT id, name FROM execution_entity LIMIT 5" --json

# Inspect Redis
n8n-factory ops redis --command "INFO" --json

# Execute a workflow (by ID)
n8n-factory ops exec --id <workflow-id> --json
```

### 3. Refactoring & Optimization
Tools to clean up existing JSON workflows.
```bash
# Normalize (fix positions, sort keys)
n8n-factory normalize my_workflow.json --output normalized.json

# Optimize (rebuild connections, remove dead code)
n8n-factory optimize my_workflow.json --output optimized.json

# Harden (add error triggers, logging)
n8n-factory harden my_workflow.json --output hardened.json --logging --error-trigger
```

## Recipe Schema (`recipes/*.yaml`)

```yaml
name: "My Workflow"
steps:
  - id: "step_1"
    template: "webhook"
    params:
      path: "my-hook"
      method: "POST"
  - id: "step_2"
    template: "code"
    params:
      code: "return items;"
```

## Best Practices
- **Reuse:** Use existing templates.
- **Validation:** Check template parameters before building.
- **Testing:** Use `n8n-factory simulate` (if implemented) or `ops exec`.
- **Debugging:** Use `n8n-factory harden` to inject logging before running.
