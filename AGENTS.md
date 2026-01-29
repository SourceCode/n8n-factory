# AI Agent Protocol: n8n-factory

**Role:** You are an autonomous specialist using `n8n-factory` to architect, deploy, and manage n8n workflows.
**Objective:** Generate valid, high-performance workflow JSONs from semantic instructions, manage their lifecycle, and optimize their execution throughput.
**Output Format:** When using CLI tools, **ALWAYS** append `--json` to receive structured, parseable data.

---

## 1. Tooling Interface (CLI)

You interact with the system via the `n8n-factory` command line.

### Core Lifecycle
| Command | Purpose | Key Arguments |
| :--- | :--- | :--- |
| `n8n-factory list --json` | **Discovery:** Get all available templates. | |
| `n8n-factory inspect <tmpl> --json` | **Discovery:** Get schema/params for a template. | `--templates <dir>` |
| `n8n-factory build <path> --json` | **Compile:** Transform YAML recipe to JSON. | `--env <name>` |
| `n8n-factory validate <path> --json` | **Verify:** Check schema and JS syntax. | `--check-env`, `--js` |
| `n8n-factory simulate <path> --json` | **Test:** Dry-run logic locally. | `--export-json <path>` |

### Operations & Control Plane
| Command | Purpose | Key Arguments |
| :--- | :--- | :--- |
| `n8n-factory queue add` | **Execute:** Schedule a workflow. | `--meta '{}'`, `--delay <ms>` |
| `n8n-factory queue list --json` | **Monitor:** Check backlog/status. | |
| `n8n-factory queue batch set` | **Tune:** Adjust batch sizes. | `max_size <int>`, `target_latency_ms <int>` |
| `n8n-factory queue gate set` | **Control:** Manage dependencies. | `<phase> --dependency <prev> --condition complete` |
| `n8n-factory ops logs --json` | **Debug:** Fetch service logs. | `--service n8n --tail 100` |

---

## 2. Workflow Construction Protocol

To build a workflow, you must generate a **Recipe** (YAML). Do not generate JSON directly.

### Step 1: Schema Definition
Create a file (e.g., `recipes/task.yaml`) with this exact structure:

```yaml
name: "Workflow Name"
description: "Clear description of purpose."
global:
  timezone: "UTC"
  # Global variables accessible via $vars
  vars:
    env: "production"

steps:
  # 1. Trigger
  - id: "trigger_node"
    template: "webhook" # See Template Library
    params:
      path: "my-endpoint"
      method: "POST"
    position: [100, 300]

  # 2. Processing
  - id: "process_data"
    template: "code"
    params:
      mode: "runOnceForAllItems"
      language: "javaScript"
      code: |
        // Use clean, modern JS. No 'any'.
        return items.map(item => ({
          json: { 
            processed: true, 
            data: item.json.body,
            timestamp: new Date().toISOString()
          }
        }));
    next: 
      - "destination_node"

  # 3. Destination
  - id: "destination_node"
    template: "slack"
    params:
      channel: "alerts"
      text: "New data: {{ $json.data }}"
```

### Step 2: Build & Validate
1.  **Build:** `n8n-factory build recipes/task.yaml --output workflows/task.json --json`
2.  **Validate:** `n8n-factory validate recipes/task.yaml --json`

---

## 3. Template Library

Select templates based on intent. Do not invent template names.

### High-Frequency Templates
| Category | Template | Key Params | Usage |
| :--- | :--- | :--- | :--- |
| **Logic** | `if` | `conditions` (complex object) | Branching execution. |
| | `switch` | `rules` (complex object) | Multi-way routing. |
| | `merge` | `mode` (append, merge, wait) | Sync branches. |
| **Data** | `set` | `values` (obj) | Simple data assignment. |
| | `code` | `code`, `language` (js/py) | Complex transformation. |
| | `split_in_batches` | `batchSize` | Loop over large datasets. |
| **I/O** | `webhook` | `path`, `method` | HTTP Trigger. |
| | `http_request` | `url`, `method`, `auth` | External API calls. |
| | `postgres` | `operation`, `query` | Database interactions. |

### AI & Vector Templates
| Category | Template | Key Params | Usage |
| :--- | :--- | :--- | :--- |
| **LLM** | `openai` | `resource`, `operation`, `prompt` | Chat/Completion. |
| | `ollama_chat` | `model`, `prompt` | Local LLM chat. |
| **Vector** | `pinecone` | `operation`, `index` | Vector search/upsert. |
| | `qdrant` | `operation`, `collection` | Self-hosted vector DB. |

*(Run `n8n-factory list --json` for the full 80+ template list)*

---

## 4. Advanced Execution Control (Control Plane)

For high-throughput or complex dependency chains, utilize the Control Plane features.

### A. Phase Gating
**Use Case:** Prevent "Phase 3" (Aggregation) from running until "Phase 2" (Processing) is complete.

**Agent Action:**
1.  **Define Dependency:**
    ```bash
    n8n-factory queue gate set "phase_3" --dependency "phase_2" --condition complete
    ```
2.  **Schedule Job with Meta:**
    ```bash
    n8n-factory queue add workflows/aggregation.json --meta '{"phase": "phase_3", "run_id": "daily_run_01"}'
    ```
    *Result:* If Phase 2 cursors are incomplete, this job is queued but **delayed** (requeued) automatically until the gate opens.

### B. Adaptive Batch Sizing
**Use Case:** Optimize throughput dynamically based on API latency or error rates.

**Agent Action:**
1.  **Inject Variable:** In your `code` node, use the environment variable `BATCH_SIZE`.
    ```javascript
    const batchSize = parseInt($env.BATCH_SIZE || '10');
    // Use this to limit API calls or chunk data
    ```
2.  **Monitor & Tune:**
    The scheduler automatically adjusts `BATCH_SIZE` based on job success/latency. You can manually override:
    ```bash
    # Set rigid bounds
    n8n-factory queue batch set max_size 50
    n8n-factory queue batch set target_latency_ms 2000
    ```

### C. Delayed Execution & Retries
**Use Case:** Rate limits or specific timing.

**Agent Action:**
1.  **Schedule with Delay:**
    ```bash
    n8n-factory queue add workflows/report.json --delay 60000 --meta '{"reason": "wait_for_api"}'
    ```
2.  **Automatic Backoff:**
    The scheduler handles retries (exponential backoff) automatically. No action needed unless you want to inspect failures:
    ```bash
    n8n-factory ops logs --service n8n --json
    # Or check structured logs in logs/jobs.jsonl
    ```

### D. Auto-Refill Strategy
**Use Case:** Keep the queue saturated from an external source (e.g., a database polling script) without overfilling it.

**Agent Action:**
1.  **Run Worker with Refill:**
    ```bash
    n8n-factory queue run --refill-cmd "python populate_queue.py" --refill-threshold 10
    ```
    *Result:* When the queue size drops below 10, the worker executes `python populate_queue.py` in the background to fetch more work.

### E. Standard Queue Metadata
When queuing jobs, populate the `meta` field with standard keys for observability and routing.

*   `run_id`: Unique correlation ID for the batch.
*   `shard_id`: Partition identifier (e.g., "shard_01").
*   `batch_size`: The intended batch size for this job.

```bash
n8n-factory queue add workflows/processor.json --meta '{"run_id": "run_123", "shard_id": "s1", "batch_size": 1}'
```

---

## 5. Debugging & Optimization Protocol

If a workflow fails or performs poorly:

1.  **Analyze Logs:**
    `n8n-factory ops analyze-logs --service n8n --json` -> Checks for crash loops or high error rates.
2.  **Inspect Queue:**
    `n8n-factory queue list --json` -> Look for high `retries` count or stuck jobs.
3.  **Local Simulation:**
    `n8n-factory simulate recipes/broken_workflow.yaml --steps 10 --json` -> fast feedback loop.
4.  **Harden:**
    `n8n-factory harden recipes/broken_workflow.yaml --logging --error-trigger --output recipes/fixed.yaml` -> Automatically injects error handling nodes.

## 6. Design Patterns

### Standard Queue/Loop Pattern
Use this pattern for robust iteration over large datasets without memory overflows.

1.  **Structure:** `Source -> SplitInBatches -> Processing -> LoopBack`
2.  **Implementation:**
    *   **SplitInBatches:** Use `batchSize: 1` for safety.
    *   **LoopBack:** Use `connections_loop` to create the cycle back to `SplitInBatches` (bypasses DAG check).
    *   **Sink:** Connect the "Done" output (index 1) to a `no_op` node.

    ```yaml
    - id: "batch_node"
      template: "split_in_batches"
      params:
        batchSize: 1
    
    - id: "process"
      template: "ollama_http_generate"
      connections_loop:
        - "batch_node" # The Loop Edge
    
    - id: "done_sink"
      template: "no_op"
      connections_from:
        - node: "batch_node"
          type: "main"
          index: 1
    ```

### Concurrency Safety
For resource-intensive nodes (e.g., local LLM inference):
1.  **Batch Size:** Always set `batchSize: 1` in `split_in_batches`.
2.  **Timeouts:** Use tiered timeouts:
    *   Expansion/Template: 180s
    *   Draft/Edit: 600s
3.  **Queue:** Use `n8n-factory queue` to manage concurrency externally if possible.

### Retry & Backoff Policy
Wrap unstable HTTP calls (like Ollama) with built-in retry settings. The `ollama_http_generate` template defaults to:
*   `retryOnFail`: true
*   `maxTries`: 3
*   `waitBetweenTries`: 5000 (5s)

### Progress Markers
For long-running jobs, write a heartbeat to Redis after each item to monitor progress without digging into n8n executions.

```yaml
- id: "mark_progress"
  template: "progress_marker"
  params:
    run_id: "{{ $vars.run_id }}"
    item_id: "{{ $json.id }}"
    status: "processed"
```

## 7. Best Practices

### Safe Slugging
When generating filenames or slugs, use the `safe_slugify` template to prevent errors with empty strings or special characters. It handles fallbacks automatically.

```yaml
- id: "slug_title"
  template: "safe_slugify"
  params:
    field: "topic"
    fallback_field: "id"
```

*   **Idempotency:** Design `code` nodes to be rerunnable. Use `run_id` from metadata to track state.
*   **Context:** Use `meta` fields when queuing to pass context (e.g., `{"shard_id": 5}`).
*   **Security:** Never put secrets in YAML. Use `{{ $env.SECRET_KEY }}` in params.
*   **Validation:** Always run `n8n-factory validate` before `queue add`.
