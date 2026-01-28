import argparse
import sys
import os
import json
import yaml
import logging
import time
from rich.console import Console
from deepdiff import DeepDiff
from .models import Recipe
from .assembler import WorkflowAssembler
from .simulator import WorkflowSimulator
from .optimizer import WorkflowOptimizer
from .normalizer import WorkflowNormalizer
from .hardener import WorkflowHardener
from .operator import SystemOperator
from .workspace.manager import WorkspaceManager
from .loops.sdd import SDDLoop
from .loops.kanban import KanbanLoop
from .commands.list_templates import list_templates
from .commands.init import init_recipe
from .commands.visualize import visualize_recipe
from .commands.watch import watch_recipe
from .commands.inspect import inspect_template
from .commands.publish import publish_workflow
from .commands.diff import diff_recipe
from .commands.validate import validate_recipe
from .commands.login import login_command
from .commands.stats import stats_command
from .commands.doctor import doctor_command
from .commands.clean import clean_command
from .commands.tree import tree_command
from .commands.search import search_templates
from .commands.profile import profile_command
from .commands.lint import lint_recipe
from .commands.template_new import template_new_command
from .commands.template_extract import template_extract_command
from .commands.info import info_command
from .commands.export import export_command
from .commands.serve import serve_command
from .commands.bundle import bundle_command
from .commands.benchmark import benchmark_command
from .commands.examples import examples_command
from .commands.creds import creds_command
from .commands.cost import cost_command
from .commands.audit import audit_command
from .commands.mock import mock_generate_command
from .commands.config import config_command
from .commands.import_workflow import import_command
from .commands.policy import policy_check_command
from .commands.doc import doc_command
from .commands.security import security_command
from .commands.health import health_command
from .commands.project import project_init_command
from .commands.telemetry_cmd import telemetry_export_command
from .logger import logger, setup_logger
from .utils import load_recipe
from .commands.ai import ask_command, list_models_command, optimize_prompt_command
from .commands.ops import ops_monitor_command
from .commands.schedule import schedule_worker_command, schedule_add_command, schedule_list_command, schedule_clear_command, schedule_run_command, schedule_reset_cursors_command, schedule_control_batch, schedule_control_gate

console = Console()

def load_config():
    config = {}
    if os.path.exists(".n8n-factory.yaml"):
        try:
            with open(".n8n-factory.yaml", 'r') as f:
                config = yaml.safe_load(f) or {}
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to load config: {e}[/yellow]")
    return config

def main():
    defaults = load_config()
    default_templates = defaults.get("templates_dir", "templates")
    default_tags = defaults.get("default_tags", [])
    
    parser = argparse.ArgumentParser(description="n8n Factory - Assemble workflows from recipes.")
    parser.add_argument("-v", "--verbose", "--debug", action="store_true", help="Enable debug logging")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Build
    build_p = subparsers.add_parser("build")
    build_p.add_argument("recipe"); build_p.add_argument("--output", "-o"); build_p.add_argument("--templates", "-t", default=default_templates); build_p.add_argument("--compact", action="store_true"); build_p.add_argument("--env"); build_p.add_argument("--redact", action="store_true")
    build_p.add_argument("--json", action="store_true")

    # Simulate
    sim_p = subparsers.add_parser("simulate")
    sim_p.add_argument("recipe"); sim_p.add_argument("--export-json"); sim_p.add_argument("--export-html"); sim_p.add_argument("--steps", type=int, default=100); sim_p.add_argument("--env"); sim_p.add_argument("--interactive", action="store_true"); sim_p.add_argument("--step", action="store_true")
    sim_p.add_argument("--export-csv")

    # Optimize
    opt_p = subparsers.add_parser("optimize")
    opt_p.add_argument("recipe"); opt_p.add_argument("--output", "-o")

    # Normalize
    norm_p = subparsers.add_parser("normalize")
    norm_p.add_argument("recipe"); norm_p.add_argument("--output", "-o")

    # Harden
    hard_p = subparsers.add_parser("harden")
    hard_p.add_argument("recipe"); hard_p.add_argument("--output", "-o"); hard_p.add_argument("--logging", action="store_true"); hard_p.add_argument("--error-trigger", action="store_true")

    # Ops
    ops_p = subparsers.add_parser("ops", help="Operations for Docker, DB, Redis, and n8n execution")
    ops_subs = ops_p.add_subparsers(dest="ops_command")

    ops_logs = ops_subs.add_parser("logs")
    ops_logs.add_argument("--service", "-s", default="n8n")
    ops_logs.add_argument("--tail", type=int, default=100)
    ops_logs.add_argument("--json", action="store_true")

    ops_db = ops_subs.add_parser("db")
    ops_db.add_argument("--query", "-q", required=True)
    ops_db.add_argument("--json", action="store_true")

    ops_redis = ops_subs.add_parser("redis")
    ops_redis.add_argument("--command", "-c", required=True, dest="redis_cmd")
    ops_redis.add_argument("--json", action="store_true")

    ops_exec = ops_subs.add_parser("exec")
    ops_exec.add_argument("--workflow-id", "--id")
    ops_exec.add_argument("--file", "-f")
    ops_exec.add_argument("--json", action="store_true")

    ops_wh = ops_subs.add_parser("webhook")
    ops_wh.add_argument("url")
    ops_wh.add_argument("--method", "-X", default="POST")
    ops_wh.add_argument("--data", "-d", default="{}")
    ops_wh.add_argument("--json", action="store_true")

    ops_ana = ops_subs.add_parser("analyze-logs")
    ops_ana.add_argument("--service", "-s", default="n8n")
    ops_ana.add_argument("--json", action="store_true")

    ops_mon = ops_subs.add_parser("monitor")
    ops_mon.add_argument("id", nargs="?", help="Execution ID to watch")
    ops_mon.add_argument("--json", action="store_true")

    # Security
    sec_p = subparsers.add_parser("security")
    sec_p.add_argument("recipe")
    sec_p.add_argument("--json", action="store_true")

    # Worker
    worker_p = subparsers.add_parser("worker")
    worker_subs = worker_p.add_subparsers(dest="worker_command")
    
    w_start = worker_subs.add_parser("start")
    w_start.add_argument("--concurrency", "-c", type=int, default=5)
    w_start.add_argument("--poll", "-p", type=int, default=5)

    # Queue
    queue_p = subparsers.add_parser("queue")
    queue_subs = queue_p.add_subparsers(dest="queue_command")
    
    q_add = queue_subs.add_parser("add")
    q_add.add_argument("workflow"); q_add.add_argument("--mode", default="id", choices=["id", "file"]); q_add.add_argument("--data", default="{}")
    q_add.add_argument("--meta", default="{}")
    q_add.add_argument("--delay", type=int, default=0, help="Delay in ms")
    
    q_run = queue_subs.add_parser("run")
    q_run.add_argument("--concurrency", "-c", type=int, default=5)
    q_run.add_argument("--poll", "-p", type=int, default=5)
    q_run.add_argument("--broker-port", type=int, help="Override broker port")
    q_run.add_argument("--refill-cmd", help="Command to execute when queue is low")
    q_run.add_argument("--refill-threshold", type=int, default=5, help="Queue size threshold for refill")

    q_list = queue_subs.add_parser("list")
    q_list.add_argument("--limit", type=int, default=20); q_list.add_argument("--json", action="store_true")
    
    q_clear = queue_subs.add_parser("clear")
    
    q_reset = queue_subs.add_parser("reset-cursors")
    q_reset.add_argument("run_id")

    q_batch = queue_subs.add_parser("batch")
    q_batch.add_argument("action", choices=["get", "set"])
    q_batch.add_argument("key", nargs="?")
    q_batch.add_argument("value", nargs="?")

    q_gate = queue_subs.add_parser("gate")
    q_gate.add_argument("action", choices=["get", "set"])
    q_gate.add_argument("phase")
    q_gate.add_argument("--dependency")
    q_gate.add_argument("--condition", default="complete")

    # List
    list_p = subparsers.add_parser("list")
    list_p.add_argument("--templates", "-t", default=default_templates); list_p.add_argument("--json", action="store_true")

    # Info
    info_p = subparsers.add_parser("info")
    info_p.add_argument("recipe")
    info_p.add_argument("--dependencies", action="store_true")
    info_p.add_argument("--json", action="store_true")

    # Export
    exp_p = subparsers.add_parser("export")
    exp_p.add_argument("recipe"); exp_p.add_argument("--format", default="yaml")

    # Template
    tmpl_p = subparsers.add_parser("template")
    tmpl_subs = tmpl_p.add_subparsers(dest="template_command")
    tmpl_new = tmpl_subs.add_parser("new")
    tmpl_new.add_argument("--output-dir", default="templates")
    tmpl_new.add_argument("--name")
    tmpl_new.add_argument("--type")
    tmpl_new.add_argument("--json", action="store_true")
    
    tmpl_ext = tmpl_subs.add_parser("extract")
    tmpl_ext.add_argument("workflow")
    tmpl_ext.add_argument("node")
    tmpl_ext.add_argument("--json", action="store_true")

    # Policy
    pol_p = subparsers.add_parser("policy")
    pol_p.add_argument("recipe")
    pol_p.add_argument("--json", action="store_true")

    # Knowledge
    subparsers.add_parser("context").add_argument("--json", action="store_true")
    subparsers.add_parser("catalog").add_argument("--json", action="store_true")
    usg_p = subparsers.add_parser("usage"); usg_p.add_argument("template"); usg_p.add_argument("--json", action="store_true")

    # Devtools
    subparsers.add_parser("backup").add_argument("--json", action="store_true")
    tst_p = subparsers.add_parser("test"); tst_p.add_argument("recipe"); tst_p.add_argument("--output", "-o"); tst_p.add_argument("--json", action="store_true")
    env_p = subparsers.add_parser("env"); env_p.add_argument("action", choices=["get", "set", "list"]); env_p.add_argument("key", nargs="?"); env_p.add_argument("value", nargs="?"); env_p.add_argument("--json", action="store_true")

    # Intelligence
    met_p = subparsers.add_parser("metrics"); met_p.add_argument("recipe"); met_p.add_argument("--json", action="store_true")
    fix_p = subparsers.add_parser("fix"); fix_p.add_argument("recipe"); fix_p.add_argument("--json", action="store_true")
    sug_p = subparsers.add_parser("suggest"); sug_p.add_argument("recipe"); sug_p.add_argument("--json", action="store_true")
    cnv_p = subparsers.add_parser("convert"); cnv_p.add_argument("file"); cnv_p.add_argument("--json", action="store_true")

    # Coverage
    cov_p = subparsers.add_parser("coverage"); cov_p.add_argument("recipe"); cov_p.add_argument("history"); cov_p.add_argument("--json", action="store_true")

    # Search
    search_p = subparsers.add_parser("search")
    search_p.add_argument("query"); search_p.add_argument("--templates", "-t", default=default_templates)
    search_p.add_argument("--json", action="store_true")

    # Init
    init_p = subparsers.add_parser("init")
    init_p.add_argument("--minimal", action="store_true")
    init_p.add_argument("--json", action="store_true")
    
    viz_p = subparsers.add_parser("visualize")
    viz_p.add_argument("recipe"); viz_p.add_argument("--format", default="mermaid")

    watch_p = subparsers.add_parser("watch")
    watch_p.add_argument("recipe"); watch_p.add_argument("--templates", "-t", default=default_templates)

    insp_p = subparsers.add_parser("inspect")
    insp_p.add_argument("template"); insp_p.add_argument("--templates", "-t", default=default_templates)
    insp_p.add_argument("--json", action="store_true")

    # Import
    imp_p = subparsers.add_parser("import")
    imp_p.add_argument("file", help="Input n8n JSON file")
    imp_p.add_argument("--output", "-o", help="Output recipe YAML")
    imp_p.add_argument("--json", action="store_true")

    pub_p = subparsers.add_parser("publish")
    pub_p.add_argument("recipe"); pub_p.add_argument("--templates", "-t", default=default_templates); pub_p.add_argument("--env")
    pub_p.add_argument("--activate", action="store_true")
    pub_p.add_argument("--json", action="store_true")

    # Run (Alias for Publish + Activate)
    run_p = subparsers.add_parser("run")
    run_p.add_argument("recipe"); run_p.add_argument("--templates", "-t", default=default_templates); run_p.add_argument("--env")
    run_p.add_argument("--json", action="store_true")

    diff_p = subparsers.add_parser("diff")
    diff_p.add_argument("recipe"); diff_p.add_argument("target"); diff_p.add_argument("--templates", "-t", default=default_templates); diff_p.add_argument("--html")
    diff_p.add_argument("--summary", action="store_true")
    diff_p.add_argument("--json", action="store_true")

    # Audit
    aud_p = subparsers.add_parser("audit")
    aud_p.add_argument("recipe")
    aud_p.add_argument("--json", action="store_true")

    # Cost
    cst_p = subparsers.add_parser("cost")
    cst_p.add_argument("recipe")
    cst_p.add_argument("--json", action="store_true")

    # Mock
    mock_p = subparsers.add_parser("mock")
    mock_p.add_argument("recipe")
    mock_p.add_argument("--output", "-o")
    mock_p.add_argument("--json", action="store_true")

    val_p = subparsers.add_parser("validate")
    val_p.add_argument("recipe"); val_p.add_argument("--templates", "-t", default=default_templates); val_p.add_argument("--env")
    val_p.add_argument("--check-env", action="store_true")
    val_p.add_argument("--js", action="store_true")
    val_p.add_argument("--json", action="store_true")

    lint_p = subparsers.add_parser("lint")
    lint_p.add_argument("recipe"); lint_p.add_argument("--templates", "-t", default=default_templates)
    lint_p.add_argument("--strict", action="store_true")
    lint_p.add_argument("--json", action="store_true")

    subparsers.add_parser("login")
    
    prof_p = subparsers.add_parser("profile")
    prof_p.add_argument("name")

    stats_p = subparsers.add_parser("stats")
    stats_p.add_argument("recipe")
    stats_p.add_argument("--json", action="store_true")

    # Creds
    creds_p = subparsers.add_parser("creds")
    creds_p.add_argument("--scaffold", action="store_true")
    creds_p.add_argument("--json", action="store_true")

    # Health
    health_p = subparsers.add_parser("health")
    health_p.add_argument("--json", action="store_true")

    # Project
    proj_p = subparsers.add_parser("project")
    proj_subs = proj_p.add_subparsers(dest="project_command")
    proj_init = proj_subs.add_parser("init")
    proj_init.add_argument("--force", action="store_true")
    proj_init.add_argument("--json", action="store_true")

    # Telemetry
    tel_p = subparsers.add_parser("telemetry")
    tel_p.add_argument("--export", action="store_true")
    tel_p.add_argument("--json", action="store_true")

    subparsers.add_parser("doctor")
    
    # Doc
    doc_p = subparsers.add_parser("doc")
    doc_p.add_argument("recipe")
    doc_p.add_argument("--prompt", action="store_true")
    doc_p.add_argument("--json", action="store_true")

    clean_p = subparsers.add_parser("clean")
    clean_p.add_argument("--json", action="store_true")
    
    config_p = subparsers.add_parser("config")
    config_p.add_argument("--json", action="store_true")
    
    tree_p = subparsers.add_parser("tree")
    tree_p.add_argument("recipe")

    serve_p = subparsers.add_parser("serve")
    serve_p.add_argument("recipe"); serve_p.add_argument("--port", type=int, default=8000)

    bun_p = subparsers.add_parser("bundle")
    bun_p.add_argument("recipe"); bun_p.add_argument("--output", default="bundle.zip")

    bench_p = subparsers.add_parser("benchmark")
    bench_p.add_argument("--size", type=int, default=1000)

    ex_p = subparsers.add_parser("examples")
    ex_p.add_argument("action", default="list", nargs="?"); ex_p.add_argument("name", nargs="?")

    # Version
    ver_p = subparsers.add_parser("version")
    ver_p.add_argument("--json", action="store_true")

    # AI
    ai_p = subparsers.add_parser("ai")
    ai_subs = ai_p.add_subparsers(dest="ai_command")
    
    ai_chat = ai_subs.add_parser("chat")
    ai_chat.add_argument("prompt")
    ai_chat.add_argument("--model", "-m")
    ai_chat.add_argument("--system", "-s")
    ai_chat.add_argument("--json", action="store_true")

    ai_list = ai_subs.add_parser("list")
    ai_list.add_argument("--json", action="store_true")

    ai_models = ai_subs.add_parser("models")
    ai_models.add_argument("--json", action="store_true")

    ai_opt = ai_subs.add_parser("optimize")
    ai_opt.add_argument("prompt")
    ai_opt.add_argument("--model", "-m")
    ai_opt.add_argument("--json", action="store_true")

    # Loop
    loop_p = subparsers.add_parser("loop")
    loop_subs = loop_p.add_subparsers(dest="loop_command")
    
    loop_init = loop_subs.add_parser("init")
    
    loop_run = loop_subs.add_parser("run")
    loop_run.add_argument("--type", choices=["sdd", "kanban"], default="sdd")
    loop_run.add_argument("--goal")
    loop_run.add_argument("--model")
    loop_run.add_argument("--max-iterations", type=int, default=25)
    loop_run.add_argument("--approve", action="store_true")
    loop_run.add_argument("--resume", action="store_true")

    loop_status = loop_subs.add_parser("status")
    loop_reset = loop_subs.add_parser("reset")
    loop_reset.add_argument("--yes", action="store_true")

    # Schema
    subparsers.add_parser("schema")

    args = parser.parse_args()

    try:
        if args.verbose:
            setup_logger(level="DEBUG")
            logger.debug("Debug logging enabled")

        if args.command == "loop":
            workspace = WorkspaceManager()
            
            if args.loop_command == "init":
                workspace.init_workspace()
                workspace.ensure_sdd_files()
                workspace.ensure_kanban_file()
                console.print("[green]Loop workspace initialized in .n8n-factory/[/green]")
            
            elif args.loop_command == "run":
                config = workspace.load_config()
                if args.model:
                    config["model"] = args.model
                
                loop = None
                if args.type == "sdd":
                    loop = SDDLoop(workspace, config, goal=args.goal, resume=args.resume)
                elif args.type == "kanban":
                    loop = KanbanLoop(workspace, config, goal=args.goal, resume=args.resume)
                
                if loop:
                    loop.run(max_iterations=args.max_iterations, approve=args.approve)

            elif args.loop_command == "status":
                if os.path.exists(".n8n-factory/state.json"):
                    with open(".n8n-factory/state.json") as f:
                        print(f.read())
                else:
                    console.print("[yellow]No active loop state found.[/yellow]")

            elif args.loop_command == "reset":
                if args.yes:
                    import shutil
                    if os.path.exists(".n8n-factory"):
                        shutil.rmtree(".n8n-factory")
                        console.print("[green]Workspace reset.[/green]")
                else:
                    console.print("[yellow]Use --yes to confirm reset.[/yellow]")

        elif args.command == "ai":
            if args.ai_command == "chat":
                ask_command(args.prompt, model=args.model, system=args.system, json_output=args.json)
            elif args.ai_command == "list" or args.ai_command == "models":
                list_models_command(json_output=args.json)
            elif args.ai_command == "optimize":
                optimize_prompt_command(args.prompt, model=args.model, json_output=args.json)
            else:
                console.print("Use: ai chat <prompt> | list | models | optimize <prompt>")

        elif args.command == "build":
            # ... existing build logic ...
            start_time = time.time()
            recipes_to_build = []
            if os.path.isdir(args.recipe):
                import glob
                recipes_to_build = glob.glob(os.path.join(args.recipe, "**/*.yaml"), recursive=True)
                if not recipes_to_build:
                    if args.json:
                        print(json.dumps({"error": "No .yaml recipes found", "path": args.recipe}))
                        sys.exit(0)
                    console.print(f"[yellow]No .yaml recipes found in {args.recipe}[/yellow]")
                    sys.exit(0)
            else:
                recipes_to_build = [args.recipe]

            built_files = []
            errors = []
            status_ctx = console.status(f"[bold green]Building {len(recipes_to_build)} workflow(s)...") if not args.json else open(os.devnull, 'w')
            
            assembler = WorkflowAssembler(templates_dir=args.templates)
            for recipe_path in recipes_to_build:
                try:
                    recipe = load_recipe(recipe_path, env_name=args.env)
                    if default_tags:
                        recipe.tags.extend(default_tags)
                        recipe.tags = list(set(recipe.tags))

                    workflow = assembler.assemble(recipe)
                    if args.redact:
                        logger.info("Redaction enabled (placeholder)")

                    if args.output:
                        if len(recipes_to_build) > 1 and not os.path.isdir(args.output):
                            if not args.json: logger.warning("Output must be a directory for multiple recipes.")
                            output_path = f"{recipe.name.replace(' ', '_').lower()}.json"
                        elif len(recipes_to_build) > 1:
                                output_path = os.path.join(args.output, f"{recipe.name.replace(' ', '_').lower()}.json")
                        else:
                            output_path = args.output
                    else:
                        output_path = f"{recipe.name.replace(' ', '_').lower()}.json"
                    
                    with open(output_path, 'w', encoding='utf-8') as f:
                        if args.compact:
                            json.dump(workflow, f, separators=(',', ':'))
                        else:
                            json.dump(workflow, f, indent=2)
                    
                    built_files.append({"recipe": recipe_path, "output": output_path})
                    if not args.json:
                        console.print(f"[bold green]Built:[/bold green] {output_path}")
                    
                except Exception as e:
                    errors.append({"recipe": recipe_path, "error": str(e)})
                    if not args.json:
                        logger.error(f"Error building {recipe_path}: {e}")
                    if len(recipes_to_build) == 1 and not args.json:
                        sys.exit(1)
            
            elapsed = time.time() - start_time
            if args.json:
                print(json.dumps({
                    "status": "success" if not errors else "partial_success",
                    "built": built_files,
                    "errors": errors,
                    "count": len(built_files),
                    "elapsed": elapsed
                }, indent=2))
                if errors and len(recipes_to_build) == 1:
                    sys.exit(1)
            elif not args.json:
                console.print(f"[dim]Finished in {elapsed:.2f}s[/dim]")

        # ... (rest of command mappings, simulate, publish, etc. - no changes needed below this point unless specific updates) ...
        # I need to ensure I didn't cut off the rest of the file logic.
        # The 'simulate', 'publish', 'run', 'optimize' etc blocks are all separate if/elif blocks.
        # I inserted the 'loop' block before 'ai' or around it.
        # The provided 'new_string' has `if args.command == "loop":` and then `elif args.command == "ai":`.
        # I should just verify the `elif` chain continues correctly for `build`, `simulate` etc.
        
        # My write_file call replaces the whole file. I need to include ALL the existing elif blocks.
        # The file I read had `elif args.command == "simulate":` etc.
        # I will include them.

        elif args.command == "simulate":
            recipe = load_recipe(args.recipe, env_name=args.env)
            simulator = WorkflowSimulator()
            history = simulator.simulate(recipe, max_steps=args.steps, interactive=args.interactive, step_mode=args.step)
            if args.export_json:
                with open(args.export_json, 'w', encoding='utf-8') as f:
                    json.dump(history, f, indent=2)
                console.print(f"[bold blue]Simulation history exported to:[/bold blue] {args.export_json}")
            if args.export_html:
                 simulator.generate_html_report(history, args.export_html)
                 console.print(f"[bold blue]HTML Report exported to:[/bold blue] {args.export_html}")
            if args.export_csv:
                 simulator.export_csv(history, args.export_csv)
                 console.print(f"[bold blue]CSV Report exported to:[/bold blue] {args.export_csv}")

        elif args.command == "publish":
            with console.status("[bold blue]Publishing...") as status:
                recipe = load_recipe(args.recipe, env_name=args.env)
                publish_workflow(recipe, args.templates, activate=args.activate, json_output=args.json)

        elif args.command == "run":
            with console.status("[bold blue]Running (Publish+Activate)...") as status:
                recipe = load_recipe(args.recipe, env_name=args.env)
                publish_workflow(recipe, args.templates, activate=True, json_output=args.json)

        elif args.command == "optimize":
            optimizer = WorkflowOptimizer()
            if args.recipe.endswith(".json"):
                with open(args.recipe, 'r', encoding='utf-8') as f:
                    workflow_data = json.load(f)
                optimized_workflow = optimizer.refactor_json(workflow_data, reinsert_edges=True)
                diff = DeepDiff(workflow_data, optimized_workflow, ignore_order=True)
                base, ext = os.path.splitext(args.recipe)
                output_path = args.output or f"{base}_optimized{ext}"
                diff_path = f"{base}_diff.txt"
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(optimized_workflow, f, indent=2)
                with open(diff_path, 'w', encoding='utf-8') as f:
                    f.write(str(diff))
                console.print(f"[bold green]Optimized workflow saved to:[/bold green] {output_path}")
            else:
                recipe = load_recipe(args.recipe)
                optimized_recipe = optimizer.optimize(recipe)
                output_path = args.output
                if not output_path:
                    base, ext = os.path.splitext(args.recipe)
                    output_path = f"{base}_optimized{ext}"
                with open(output_path, 'w', encoding='utf-8') as f:
                    yaml.dump(optimized_recipe.model_dump(), f, sort_keys=False)
                console.print(f"[bold green]Optimized recipe saved to:[/bold green] {output_path}")

        elif args.command == "normalize":
            normalizer = WorkflowNormalizer()
            output_path = args.output
            if args.recipe.endswith(".json"):
                 with open(args.recipe, 'r', encoding='utf-8') as f:
                    workflow_data = json.load(f)
                 normalized = normalizer.normalize_json(workflow_data)
                 if not output_path:
                     base, ext = os.path.splitext(args.recipe)
                     output_path = f"{base}_normalized{ext}"
                 with open(output_path, 'w', encoding='utf-8') as f:
                     json.dump(normalized, f, indent=2)
            else:
                recipe = load_recipe(args.recipe)
                normalized = normalizer.normalize_recipe(recipe)
                if not output_path:
                     base, ext = os.path.splitext(args.recipe)
                     output_path = f"{base}_normalized{ext}"
                with open(output_path, 'w', encoding='utf-8') as f:
                    yaml.dump(normalized.model_dump(), f, sort_keys=False)
            console.print(f"[bold green]Normalized output saved to:[/bold green] {output_path}")

        elif args.command == "harden":
            hardener = WorkflowHardener()
            output_path = args.output
            if args.recipe.endswith(".json"):
                 with open(args.recipe, 'r', encoding='utf-8') as f:
                    workflow_data = json.load(f)
                 hardened = hardener.harden_json(workflow_data, add_logging=args.logging, add_error_trigger=args.error_trigger)
                 if not output_path:
                     base, ext = os.path.splitext(args.recipe)
                     output_path = f"{base}_hardened{ext}"
                 with open(output_path, 'w', encoding='utf-8') as f:
                     json.dump(hardened, f, indent=2)
            else:
                recipe = load_recipe(args.recipe)
                hardened = hardener.harden_recipe(recipe, add_logging=args.logging, add_error_trigger=args.error_trigger)
                if not output_path:
                     base, ext = os.path.splitext(args.recipe)
                     output_path = f"{base}_hardened{ext}"
                with open(output_path, 'w', encoding='utf-8') as f:
                    yaml.dump(hardened.model_dump(), f, sort_keys=False)
            console.print(f"[bold green]Hardened output saved to:[/bold green] {output_path}")

        elif args.command == "security":
            recipe = load_recipe(args.recipe)
            security_command(recipe, json_output=args.json)

        elif args.command == "ops":
            operator = SystemOperator()
            output = None
            if args.ops_command == "logs":
                logs = operator.get_logs(args.service, args.tail)
                output = {"service": args.service, "logs": logs}
            elif args.ops_command == "db":
                results = operator.run_db_query(args.query)
                output = {"query": args.query, "results": results}
            elif args.ops_command == "redis":
                res = operator.inspect_redis(args.redis_cmd)
                output = {"command": args.redis_cmd, "result": res}
            elif args.ops_command == "exec":
                res = operator.execute_workflow(args.workflow_id, args.file)
                output = {"execution_result": res}
            elif args.ops_command == "webhook":
                try:
                    data = json.loads(args.data)
                except:
                    data = {}
                res = operator.trigger_webhook(args.method, args.url, data)
                output = {"result": res}
            elif args.ops_command == "analyze-logs":
                res = operator.analyze_logs(args.service)
                output = res
            elif args.ops_command == "monitor":
                ops_monitor_command(watch_id=args.id, json_output=args.json)
                sys.exit(0) # Exit here as monitor handles its own output
            else:
                parser.print_help()
                sys.exit(0)
            
            if args.json or args.ops_command in ["db", "analyze-logs"]:
                 print(json.dumps(output, indent=2))
            else:
                 console.print(output)

        elif args.command == "worker":
            if args.worker_command == "start":
                schedule_worker_command(concurrency=args.concurrency, poll=args.poll)
            else:
                console.print("Use: worker start")
        
        elif args.command == "queue":
            if args.queue_command == "add":
                schedule_add_command(args.workflow, args.mode, args.data, args.meta, args.delay)
            elif args.queue_command == "run":
                schedule_run_command(
                    concurrency=args.concurrency, 
                    poll=args.poll, 
                    broker_port=args.broker_port,
                    refill_cmd=args.refill_cmd,
                    refill_threshold=args.refill_threshold
                )
            elif args.queue_command == "list":
                schedule_list_command(args.limit, args.json)
            elif args.queue_command == "clear":
                schedule_clear_command()
            elif args.queue_command == "reset-cursors":
                schedule_reset_cursors_command(args.run_id)
            elif args.queue_command == "batch":
                schedule_control_batch(args.action, args.key, args.value)
            elif args.queue_command == "gate":
                schedule_control_gate(args.action, args.phase, args.dependency, args.condition)
            else:
                console.print("Use: queue add | list | clear | reset-cursors | batch | gate")

        elif args.command == "list": list_templates(args.templates, json_output=args.json)
        elif args.command == "info": info_command(args.recipe, dependencies=args.dependencies, json_output=args.json)
        elif args.command == "export": export_command(args.recipe, args.format)
        elif args.command == "search": search_templates(args.query, args.templates, json_output=args.json)
        elif args.command == "init": init_recipe(minimal=args.minimal, json_output=args.json)
        elif args.command == "visualize": 
            recipe = load_recipe(args.recipe)
            visualize_recipe(recipe, format=args.format)
        elif args.command == "watch": watch_recipe(args.recipe, args.templates)
        elif args.command == "inspect": inspect_template(args.template, args.templates, json_output=args.json)
        elif args.command == "diff": diff_recipe(args.recipe, args.target, args.templates, html_output=args.html, summary=args.summary, json_output=args.json)

        elif args.command == "import": import_command(args.file, args.output, args.json)

        elif args.command == "cost": cost_command(args.recipe, json_output=args.json)

        elif args.command == "mock": mock_generate_command(args.recipe, args.output, json_output=args.json)

        elif args.command == "audit": audit_command(args.recipe, json_output=args.json)

        elif args.command == "validate":
            recipe = load_recipe(args.recipe, env_name=args.env)
            validate_recipe(recipe, args.templates, check_env=args.check_env, check_js=args.js, json_output=args.json)

        elif args.command == "lint":
            recipe = load_recipe(args.recipe)
            lint_recipe(recipe, args.templates, strict=args.strict, json_output=args.json)
        elif args.command == "login": login_command()
        elif args.command == "profile": profile_command(args.name)
        elif args.command == "stats":
            recipe = load_recipe(args.recipe)
            stats_command(recipe, json_output=args.json)
        elif args.command == "doctor": doctor_command()
        elif args.command == "clean": clean_command(json_output=args.json)
        elif args.command == "config": config_command(json_output=args.json)

        elif args.command == "doc": 
            recipe = load_recipe(args.recipe)
            doc_command(recipe, json_output=args.json, prompt_mode=args.prompt)

        elif args.command == "tree":
            recipe = load_recipe(args.recipe)
            tree_command(recipe)

        elif args.command == "serve": serve_command(args.recipe, port=args.port)

        elif args.command == "benchmark": benchmark_command(args.size)
        elif args.command == "bundle": bundle_command(args.recipe, args.output)
        elif args.command == "examples": examples_command(args.action, args.name)
        elif args.command == "creds": creds_command(scaffold=args.scaffold, json_output=args.json)
        elif args.command == "health": health_command(json_output=args.json)
        elif args.command == "project":
            if args.project_command == "init":
                project_init_command(force=args.force, json_output=args.json)
            else:
                console.print("Use: project init")
        elif args.command == "telemetry":
            if args.export:
                telemetry_export_command(json_output=args.json)
            else:
                console.print("Use: telemetry --export")
        elif args.command == "template":
            if args.template_command == "new":
                template_new_command(
                    output_dir=args.output_dir,
                    name=args.name,
                    node_type=args.type,
                    json_output=args.json
                )
            elif args.template_command == "extract":
                template_extract_command(args.workflow, args.node, json_output=args.json)
            else:
                console.print("Use: template new | extract")
        
        elif args.command == "policy":
            recipe = load_recipe(args.recipe)
            policy_check_command(recipe, json_output=args.json)
            
        elif args.command == "context": context_command(json_output=args.json)
        elif args.command == "catalog": catalog_command(json_output=args.json)
        elif args.command == "usage": usage_command(args.template, json_output=args.json)
        
        elif args.command == "backup": backup_command(json_output=args.json)
        elif args.command == "test": test_scaffold_command(args.recipe, args.output, json_output=args.json)
        elif args.command == "env": env_command(args.action, args.key, args.value, json_output=args.json)
        
        elif args.command == "metrics": metrics_command(args.recipe, json_output=args.json)
        elif args.command == "fix": fix_command(args.recipe, json_output=args.json)
        elif args.command == "suggest": suggest_command(args.recipe, json_output=args.json)
        elif args.command == "convert": convert_command(args.file, json_output=args.json)
        
        elif args.command == "coverage": 
            recipe = load_recipe(args.recipe)
            coverage_command(recipe, args.history, json_output=args.json)

        elif args.command == "ai":
            if args.ai_command == "chat":
                ask_command(args.prompt, model=args.model, system=args.system, json_output=args.json)
            elif args.ai_command == "list" or args.ai_command == "models":
                list_models_command(json_output=args.json)
            elif args.ai_command == "optimize":
                optimize_prompt_command(args.prompt, model=args.model, json_output=args.json)
            else:
                console.print("Use: ai chat <prompt> | list | models | optimize <prompt>")

        elif args.command == "schema":
             print(json.dumps(Recipe.model_json_schema(), indent=2))
        elif args.command == "version":
             ver = "1.7.0"
             if args.json:
                 print(json.dumps({"version": ver}))
             else:
                 console.print(f"n8n-factory v{ver}")
        else:
            parser.print_help()

    except Exception as e:
        if hasattr(args, 'json') and args.json:
            err = {"error": True, "type": type(e).__name__, "message": str(e)}
            print(json.dumps(err))
            sys.exit(1)
        else:
            raise e

if __name__ == "__main__":
    main()