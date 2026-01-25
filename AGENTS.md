# AI Agent Guide for n8n-factory

This document guides AI agents on how to use `n8n-factory` to construct n8n workflows.

## core_concept
Instead of writing raw, monolithic JSON for n8n, you construct **Recipes** (YAML) that reference **Templates**. The factory then assembles these into valid `workflow.json` files.

## Workflow Generation Process

1.  **Analyze Request:** Understand what the user wants the workflow to do.
2.  **Explore Templates:** List files in `templates/` (`n8n-factory list`) to see available building blocks. Use `inspect` to see details.
3.  **Create Recipe:** Write a YAML file (e.g., `recipes/my_workflow.yaml`) defining the sequence of nodes.
4.  **Build:** Run the factory command: `n8n-factory build recipes/my_workflow.yaml`.
5.  **Deliver:** The output will be `my_workflow.json` (or similar).

## Recipe Schema (`recipes/*.yaml`)

```yaml
name: "My Awesome Workflow"
description: "Description of what it does"
tags: ["category"]
globals:
  api_url: "https://api.example.com"

steps:
  - id: "step_1"
    template: "webhook"
    params:
      path: "my-webhook-url"
      method: "POST"
    notes: "Entry point"

  - id: "step_2"
    template: "http_request"
    params:
      url: "{{ api_url }}/data"
      method: "GET"
    retry:
      maxTries: 3
      waitBetweenTries: 1000
      
  - id: "step_3"
    template: "if"
    params:
      left: "={{ $json.status }}"
      right: "success"
      operator: "equal"
```

## AI Capabilities
- **Ollama:** Use `ollama_chat`, `ollama_generate`, `ollama_embeddings` templates.
- **RAG:** Use `vector_store_upsert`, `vector_store_retrieve`.
- **Utilities:** `json_parser_ai`, `summarize_text`, `classification_prompt`.

## Simulation & Testing
- Run `n8n-factory simulate recipes/my.yaml` to verify logic.
- Add `mock` data to steps for simulation.
- Use `assertions: ["output[0].json.success == true"]` in recipe for automated checks.

## Best Practices
- **Reuse:** Always check for existing templates before trying to invent a "custom" node configuration.
- **Naming:** Give steps meaningful `id`s.
- **Validation:** If the factory build fails, check your parameter names against the template variables.
- **Secrets:** Do not put secrets in recipes. Use `${ENV_VAR}` syntax or `globals`.