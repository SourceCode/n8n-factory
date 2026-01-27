# AI Agent Guide for n8n-factory

This document is the definitive guide for AI agents utilizing the `n8n-factory`. It details the architecture, CLI commands, and the comprehensive library of templates available for constructing n8n workflows.

## Core Concept

The `n8n-factory` allows you to generate valid n8n `workflow.json` files by writing simplified YAML "Recipes". These recipes reference reusable "Templates" (partial JSON configurations of n8n nodes). This approach ensures consistency, reduces errors, and simplifies the creation of complex workflows.

## Workflow Construction

To build a workflow:

1.  **Identify the Goal:** Determine the logic and services required (e.g., "Receive a webhook, process data with AI, and post to Slack").
2.  **Select Templates:** Choose the appropriate templates from the library below.
3.  **Draft Recipe:** Create a YAML file in the `recipes/` directory defining the nodes and their connections.
4.  **Build:** Execute the build command to generate the final JSON.

### Recipe Schema

Recipes are YAML files with the following structure:

```yaml
name: "My Workflow Name"
# Optional global settings
global:
  timezone: "UTC"

# Define the nodes in the workflow
steps:
  - id: "webhook_trigger"       # Unique ID for this step
    template: "webhook"         # Name of the template to use (see Library below)
    # Parameters to inject into the template
    params:
      path: "my-endpoint"
      method: "POST"
    # Position in the UI (optional, auto-layout is available)
    position: [100, 300]
    
  - id: "process_data"
    template: "code"
    params:
      mode: "runOnceForAllItems"
      language: "javaScript"
      code: |
        return items.map(item => {
          return { json: { processed: true, data: item.json } };
        });
    # Define connections: "next" defaults to the next step in the list if omitted
    next: 
      - "send_slack"

  - id: "send_slack"
    template: "slack"
    params:
      channel: "alerts"
      text: "Data processed successfully."
```

## Template Library

The following templates are available in the `templates/` directory. Use the **Template Name** in your recipes.

### Triggers & Flow Control
| Template Name | Description |
| :--- | :--- |
| `webhook` | Starts workflow on HTTP request. Params: `path`, `method`. |
| `schedule` | Triggers on a time interval. Params: `rule`. |
| `cron` | Triggers on a cron expression. |
| `start` | Manual trigger for testing. |
| `error_trigger` | Triggers when another workflow fails. |
| `respond_to_webhook` | Sends a response back to the webhook caller. |
| `wait` | Pauses execution for a set time. |
| `if` | Conditional logic (Boolean). |
| `switch` | Routing logic based on values. |
| `merge` | Merges multiple branches of execution. |
| `split_in_batches` | Loops over items in batches. |
| `stop_and_error` | Forces the workflow to stop with an error. |
| `execute_workflow` | Calls another n8n workflow. |
| `execute_command` | Runs a shell command (if allowed). |
| `no_op` | Does nothing (pass-through). |

### Core Logic & Data Transformation
| Template Name | Description |
| :--- | :--- |
| `set` | Sets values on items. |
| `set_multi` | Sets multiple values. |
| `code` | Executes JavaScript or Python code. |
| `http_request` | Makes an HTTP request. Params: `url`, `method`. |
| `function` | Legacy code node (use `code`). |
| `json_clean` | Cleans JSON data. |
| `json_diff` | Compares JSON objects. |
| `json_parser_ai` | Uses AI to parse JSON. |
| `json_validate_schema` | Validates JSON against a schema. |
| `json_extract_paths` | Extracts specific paths from JSON. |
| `json_flatten` | Flattens nested JSON. |
| `json_unflatten` | Unflattens JSON. |
| `json_pick` | Picks specific keys. |
| `json_omit` | Omits specific keys. |
| `json_array_unique` | Removes duplicates from an array. |
| `json_deep_merge` | Deep merges JSON objects. |
| `rename_keys` | Renames keys in JSON objects. |
| `item_lists` | Manages lists of items (sort, limit, etc.). |
| `compare_datasets` | Compares two datasets. |
| `crypto` | Cryptographic operations. |
| `date_time` | Date and time manipulation. |
| `html_extract` | Extracts data from HTML. |
| `xml` | XML parsing and creation. |
| `xml_to_json` | Converts XML to JSON. |
| `markdown` | Renders Markdown. |
| `markdown_to_text` | Converts Markdown to plain text. |
| `spreadsheet_file` | Reads/Writes spreadsheet files. |
| `read_binary_file` | Reads a file from disk. |
| `write_binary_file` | Writes a file to disk. |
| `move_binary_data` | Moves binary data between keys. |
| `compression` | Compresses/Decompresses data. |

### AI & Machine Learning
| Template Name | Description |
| :--- | :--- |
| `openai` | OpenAI API integration (Chat, Image, etc.). |
| `ollama_chat` | Chat with local LLMs via Ollama. |
| `ollama_generate` | Generate text with local LLMs. |
| `ollama_embeddings` | Generate embeddings with local LLMs. |
| `ollama_model_list` | List available Ollama models. |
| `ollama_model_pull` | Pull Ollama models. |
| `langchain_agent` | LangChain agent integration. |
| `vector_store_retrieve` | Retrieve data from a vector store. |
| `vector_store_upsert` | Upsert data into a vector store. |
| `pinecone` | Pinecone vector database. |
| `qdrant` | Qdrant vector database. |
| `weaviate` | Weaviate vector database. |
| `redis` | Redis (supports vector search). |
| `classification_prompt` | Classifies text using an LLM. |
| `sentiment_analysis_local` | Local sentiment analysis. |
| `summarize_text` | Summarizes text using an LLM. |
| `text_splitter` | Splits text into chunks. |
| `recursive_character_splitter` | Recursively splits text. |
| `rag_context_merge` | Merges context for RAG applications. |
| `prompt_template` | Manages prompt templates. |
| `output_parser` | Parses LLM output. |
| `memory_buffer` | Manages conversation memory. |

### Productivity & SaaS
| Template Name | Description |
| :--- | :--- |
| `slack` | Send messages to Slack. |
| `discord` | Send messages to Discord. |
| `telegram` | Send messages to Telegram. |
| `mattermost` | Mattermost integration. |
| `rocket_chat` | Rocket.Chat integration. |
| `microsoft_teams` | Microsoft Teams integration. |
| `gmail` | Send/Receive emails via Gmail. |
| `google_calendar` | Manage Google Calendar events. |
| `google_contacts` | Manage Google Contacts. |
| `google_docs` | Manage Google Docs. |
| `google_drive` | Manage Google Drive files. |
| `google_sheets` | Read/Write Google Sheets. |
| `google_tasks` | Manage Google Tasks. |
| `microsoft_outlook` | Microsoft Outlook integration. |
| `onedrive` | Microsoft OneDrive integration. |
| `notion` | Notion integration (Pages, Databases). |
| `trello` | Trello integration. |
| `asana` | Asana integration. |
| `clickup` | ClickUp integration. |
| `monday` | Monday.com integration. |
| `jira` | Jira Software integration. |
| `zendesk` | Zendesk Support integration. |
| `freshdesk` | Freshdesk integration. |
| `intercom` | Intercom integration. |
| `salesforce` | Salesforce CRM integration. |
| `hubspot` | HubSpot CRM integration. |
| `pipedrive` | Pipedrive CRM integration. |
| `active_campaign` | ActiveCampaign integration. |
| `mailchimp` | Mailchimp integration. |
| `mautic` | Mautic integration. |
| `gotify` | Send notifications via Gotify. |
| `pushover` | Send notifications via Pushover. |
| `twilio` | Send SMS/Messages via Twilio. |

### Developer Tools & Infrastructure
| Template Name | Description |
| :--- | :--- |
| `github` | GitHub integration (Issues, PRs, etc.). |
| `gitlab` | GitLab integration. |
| `jenkins` | Jenkins CI integration. |
| `circleci` | CircleCI integration. |
| `sentry` | Sentry issue tracking. |
| `pagerduty` | PagerDuty incident management. |
| `docker` | Manage Docker containers (via Execute Command or API). |
| `ssh` | Execute commands via SSH. |
| `sftp` | SFTP file transfer. |
| `ftp` | FTP file transfer. |
| `graphql` | Make GraphQL requests. |
| `mqtt` | MQTT messaging. |
| `amqp` | AMQP messaging. |
| `kafka` | Apache Kafka integration. |
| `rabbitmq` | RabbitMQ integration. |
| `s3` | AWS S3 storage. |
| `lambda` | AWS Lambda execution. |
| `dynamodb` | AWS DynamoDB. |
| `sns` | AWS SNS notifications. |
| `digital_ocean` | DigitalOcean infrastructure. |
| `postgres` | PostgreSQL database. |
| `mysql` | MySQL database. |
| `mongodb` | MongoDB database. |
| `elasticsearch` | Elasticsearch integration. |
| `snowflake` | Snowflake data warehouse. |
| `supabase` | Supabase integration. |

### Social Media
| Template Name | Description |
| :--- | :--- |
| `twitter` | Twitter/X integration. |
| `facebook` | Facebook Graph API. |
| `linkedin` | LinkedIn integration. |
| `reddit` | Reddit integration. |
| `medium` | Medium publication. |
| `pinterest` | Pinterest integration. |
| `line` | LINE Messenger integration. |

### Finance & E-commerce
| Template Name | Description |
| :--- | :--- |
| `stripe` | Stripe payments. |
| `shopify` | Shopify e-commerce. |
| `woocommerce` | WooCommerce. |
| `quickbooks` | QuickBooks Online. |
| `xero` | Xero Accounting. |

### Miscellaneous
| Template Name | Description |
| :--- | :--- |
| `rss` | Read RSS feeds. |
| `sticky_note` | Adds a sticky note to the workflow canvas. |
| `debug_logger` | Logs data to the console for debugging. |
| `filter` | Filters items based on conditions. |
| `raw` | Raw JSON node configuration. |

## CLI Commands for Agents

**Always** use the `--json` flag to receive structured output.

### Discovery
*   `n8n-factory list --json`: Returns a list of all available templates.
*   `n8n-factory search "query" --json`: Searches for templates matching the query.
*   `n8n-factory inspect <template_name> --json`: Returns the parameter schema for a specific template.

### Operations
*   `n8n-factory build <recipe_path> --json`: Compiles a recipe into a workflow JSON.
*   `n8n-factory build <recipe_path> --env production --json`: Builds with environment-specific variables.
*   `n8n-factory simulate <recipe_path> --export-html report.html --export-csv report.csv --json`: Simulates a recipe and exports reports.
*   `n8n-factory ops logs --service n8n --tail 50 --json`: Retrieves n8n service logs.
*   `n8n-factory ops exec --id <workflow_id> --json`: Executes a deployed workflow.
*   `n8n-factory optimize <workflow_path> --output <output_path>`: Optimizes an existing workflow file.
*   `n8n-factory harden <workflow_path> --output <output_path> --logging --error-trigger`: Adds error handling and logging to a workflow.

### Management & Scheduling
*   `n8n-factory login`: Interactive login to setup `.env` (use non-interactively via env vars if possible).
*   `n8n-factory stats <recipe_path> --json`: Displays metrics for a recipe.
*   `n8n-factory creds --scaffold --json`: Generates credential placeholders.
*   `n8n-factory worker start --concurrency 5`: Starts a background worker for queued jobs.
*   `n8n-factory queue add <workflow_id> --json`: Adds a job to the execution queue.
*   `n8n-factory queue list --json`: Lists pending jobs.

## Best Practices for Agents

1.  **Prefer Templates:** Always check for an existing template before using a generic `http_request` or `code` node.
2.  **Validate Parameters:** Use `inspect` to check which parameters a template accepts.
3.  **Modularize:** Break complex logic into smaller steps or separate workflows.
4.  **Error Handling:** Always include an `error_trigger` workflow or error handling logic for critical paths.
5.  **Secure Secrets:** Do not hardcode API keys or secrets in recipes. Use n8n credentials or environment variables where possible.