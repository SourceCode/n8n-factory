# n8n-factory

[![CI](https://github.com/username/n8n-factory/actions/workflows/ci.yml/badge.svg)](https://github.com/username/n8n-factory/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**n8n-factory** is a robust "Infrastructure as Code" (IaC) tool for assembling, optimizing, simulating, and publishing n8n workflows. It allows you to define complex workflows using simple, composable YAML "recipes" and reusable JSON templates.

Designed for AI agents and power users who need deterministic, scalable, and maintainable workflow generation.

## Features

*   **Assembly:** Compile YAML `recipes` into valid n8n `workflow.json` files.
*   **Templates:** Extensive library of over 80 reusable node templates covering major services and logic.
*   **Validation:** Detects circular imports, orphan nodes, and potential secrets.
*   **Optimization:** Automatically merges nodes, prunes dead code, and standardizes JSON structure.
*   **Hardening:** Inject error triggers and debug logging automatically.
*   **Simulation:** Dry-run workflows locally with mock data and export HTML/CSV reports.
*   **Operations:** Manage Docker, Postgres, and Redis directly via CLI.
*   **Bundle & Publish:** Export to ZIP or upload directly to your n8n instance API.
*   **AI Assistance:** Optimize prompts and leverage local LLMs (Ollama).
*   **Monitoring & Scheduling:** Real-time execution monitoring and job queuing.
*   **Environment Config:** Load environment-specific settings with `--env`.

## Installation

```bash
pip install n8n-factory
```

## Quick Start

1.  **Initialize:**
    ```bash
    n8n-factory init
    ```

2.  **Create Recipe:**
    Edit `recipes/my_workflow.yaml` to define your workflow logic.

3.  **Build:**
    ```bash
    n8n-factory build recipes/my_workflow.yaml
    ```

## CLI Reference

*   `build`: Assemble recipe to JSON.
*   `list`: Show available templates (`--json`).
*   `ops`: Runtime operations (`logs`, `db`, `redis`, `exec`, `monitor`).
*   `normalize`: Standardize JSON structure.
*   `optimize`: Refactor and clean up workflows.
*   `harden`: Inject debug logging and error handling.
*   `simulate`: Run logic locally (export to HTML/CSV).
*   `diff`: Compare recipe vs JSON.
*   `ai`: AI tools (chat, list models, optimize prompts).
*   `worker`: Start the workflow scheduler worker.
*   `queue`: Manage the job queue.
*   `login`: Setup environment configuration.
*   `stats`: View workflow metrics.
*   `creds`: Manage/scaffold credentials.

See `n8n-factory --help` for all commands.

## AI Features

n8n-factory integrates with [Ollama](https://ollama.ai/) to provide local AI capabilities.

### Configuration
Create a `.env` file:
```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_API_KEY=your_key_here
```

### Prompt Optimization
Refine your prompts for better AI responses:
```bash
n8n-factory ai optimize "Generate a workflow that connects gmail to slack"
```

## Monitoring & Scheduling

### Real-time Monitoring
Monitor active executions directly from the n8n database:
```bash
# List active executions
n8n-factory ops monitor

# Watch a specific execution live
n8n-factory ops monitor <EXECUTION_ID>
```

### Job Queue & Worker
Queue workflows for execution and let the worker manage concurrency.

**Start the Worker:**
```bash
n8n-factory worker start --concurrency 5
```

**Queue a Job:**
```bash
n8n-factory queue add my_workflow_id --mode id
```

**Manage Queue:**
```bash
n8n-factory queue list
n8n-factory queue clear
```

## Docker Environment

A `docker-compose.yaml` is provided to spin up a full n8n stack with Postgres and Redis (exposed on port 16552).

```bash
docker-compose up -d
```
*   **n8n**: http://localhost:5678
*   **Redis**: localhost:16552

## Architecture

The system follows a linear pipeline:
1.  **Recipe Input:** The user or AI defines the intent in `recipe.yaml`.
2.  **Assembler:** The factory combines the recipe with JSON Templates.
3.  **Optimizer:** The resulting structure is cleaned and optimized.
4.  **Output:** A valid n8n Workflow JSON is produced.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute to this project.

## License

MIT