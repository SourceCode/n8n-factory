import argparse
import sys
import os
import json
import yaml
import logging
import time
from rich.console import Console
from .models import Recipe
from .assembler import WorkflowAssembler
from .simulator import WorkflowSimulator
from .optimizer import WorkflowOptimizer
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
from .commands.info import info_command
from .commands.export import export_command
from .commands.serve import serve_command
from .commands.bundle import bundle_command
from .commands.benchmark import benchmark_command
from .commands.examples import examples_command
from .logger import logger, setup_logger
from .utils import load_recipe

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

    # Simulate
    sim_p = subparsers.add_parser("simulate")
    sim_p.add_argument("recipe"); sim_p.add_argument("--export-json"); sim_p.add_argument("--export-html"); sim_p.add_argument("--steps", type=int, default=100); sim_p.add_argument("--env"); sim_p.add_argument("--interactive", action="store_true"); sim_p.add_argument("--step", action="store_true")
    sim_p.add_argument("--export-csv")

    # Optimize
    opt_p = subparsers.add_parser("optimize")
    opt_p.add_argument("recipe"); opt_p.add_argument("--output", "-o")

    # List
    list_p = subparsers.add_parser("list")
    list_p.add_argument("--templates", "-t", default=default_templates); list_p.add_argument("--json", action="store_true")

    # Info
    info_p = subparsers.add_parser("info")
    info_p.add_argument("recipe")

    # Export
    exp_p = subparsers.add_parser("export")
    exp_p.add_argument("recipe"); exp_p.add_argument("--format", default="yaml")

    # Template
    tmpl_p = subparsers.add_parser("template")
    tmpl_subs = tmpl_p.add_subparsers(dest="template_command")
    tmpl_new = tmpl_subs.add_parser("new"); tmpl_new.add_argument("--output-dir", default="templates")

    # Search
    search_p = subparsers.add_parser("search")
    search_p.add_argument("query"); search_p.add_argument("--templates", "-t", default=default_templates)

    subparsers.add_parser("init")
    
    viz_p = subparsers.add_parser("visualize")
    viz_p.add_argument("recipe"); viz_p.add_argument("--format", default="mermaid")

    watch_p = subparsers.add_parser("watch")
    watch_p.add_argument("recipe"); watch_p.add_argument("--templates", "-t", default=default_templates)

    insp_p = subparsers.add_parser("inspect")
    insp_p.add_argument("template"); insp_p.add_argument("--templates", "-t", default=default_templates)

    pub_p = subparsers.add_parser("publish")
    pub_p.add_argument("recipe"); pub_p.add_argument("--templates", "-t", default=default_templates); pub_p.add_argument("--env")
    pub_p.add_argument("--activate", action="store_true")

    # Run (Alias for Publish + Activate)
    run_p = subparsers.add_parser("run")
    run_p.add_argument("recipe"); run_p.add_argument("--templates", "-t", default=default_templates); run_p.add_argument("--env")

    diff_p = subparsers.add_parser("diff")
    diff_p.add_argument("recipe"); diff_p.add_argument("target"); diff_p.add_argument("--templates", "-t", default=default_templates); diff_p.add_argument("--html")

    val_p = subparsers.add_parser("validate")
    val_p.add_argument("recipe"); val_p.add_argument("--templates", "-t", default=default_templates); val_p.add_argument("--env")

    lint_p = subparsers.add_parser("lint")
    lint_p.add_argument("recipe"); lint_p.add_argument("--templates", "-t", default=default_templates)

    subparsers.add_parser("login")
    
    prof_p = subparsers.add_parser("profile")
    prof_p.add_argument("name")

    stats_p = subparsers.add_parser("stats")
    stats_p.add_argument("recipe")

    subparsers.add_parser("doctor")
    subparsers.add_parser("clean")
    
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

    args = parser.parse_args()

    if args.verbose:
        setup_logger(level="DEBUG")
        logger.debug("Debug logging enabled")

    if args.command == "build":
        start_time = time.time()
        with console.status("[bold green]Building workflow...") as status:
            recipe = load_recipe(args.recipe, env_name=args.env)
            if default_tags:
                recipe.tags.extend(default_tags)
                recipe.tags = list(set(recipe.tags))

            assembler = WorkflowAssembler(templates_dir=args.templates)
            
            try:
                workflow = assembler.assemble(recipe)
                if args.redact:
                    logger.info("Redaction enabled (placeholder)")

                output_path = args.output or f"{recipe.name.replace(' ', '_').lower()}.json"
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    if args.compact:
                        json.dump(workflow, f, separators=(',', ':'))
                    else:
                        json.dump(workflow, f, indent=2)
                
                elapsed = time.time() - start_time
                console.print(f"[bold green]Successfully built workflow:[/bold green] {output_path} [dim]({elapsed:.2f}s)[/dim]")
                
            except Exception as e:
                logger.error(f"Error building workflow: {e}")
                sys.exit(1)

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
            publish_workflow(recipe, args.templates, activate=args.activate)

    elif args.command == "run":
        # Alias for Publish + Activate
        with console.status("[bold blue]Running (Publish+Activate)...") as status:
            recipe = load_recipe(args.recipe, env_name=args.env)
            publish_workflow(recipe, args.templates, activate=True)

    elif args.command == "optimize":
        recipe = load_recipe(args.recipe)
        optimizer = WorkflowOptimizer()
        optimized_recipe = optimizer.optimize(recipe)
        output_path = args.output
        if not output_path:
            base, ext = os.path.splitext(args.recipe)
            output_path = f"{base}_optimized{ext}"
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(optimized_recipe.model_dump(), f, sort_keys=False)
        console.print(f"[bold green]Optimized recipe saved to:[/bold green] {output_path}")

    elif args.command == "list": list_templates(args.templates, json_output=args.json)
    elif args.command == "info": info_command(args.recipe)
    elif args.command == "export": export_command(args.recipe, args.format)
    elif args.command == "search": search_templates(args.query, args.templates)
    elif args.command == "init": init_recipe()
    elif args.command == "visualize": 
        recipe = load_recipe(args.recipe)
        visualize_recipe(recipe, format=args.format)
    elif args.command == "watch": watch_recipe(args.recipe, args.templates)
    elif args.command == "inspect": inspect_template(args.template, args.templates)
    elif args.command == "diff": diff_recipe(args.recipe, args.target, args.templates, html_output=args.html)
    elif args.command == "validate":
        recipe = load_recipe(args.recipe, env_name=args.env)
        validate_recipe(recipe, args.templates)
    elif args.command == "lint":
        recipe = load_recipe(args.recipe)
        lint_recipe(recipe, args.templates)
    elif args.command == "login": login_command()
    elif args.command == "profile": profile_command(args.name)
    elif args.command == "stats":
        recipe = load_recipe(args.recipe)
        stats_command(recipe)
    elif args.command == "doctor": doctor_command()
    elif args.command == "clean": clean_command()
    elif args.command == "tree":
        recipe = load_recipe(args.recipe)
        tree_command(recipe)
    elif args.command == "benchmark": benchmark_command(args.size)
    elif args.command == "bundle": bundle_command(args.recipe, args.output)
    elif args.command == "examples": examples_command(args.action, args.name)
    elif args.command == "template":
        if args.template_command == "new":
            template_new_command(args.output_dir)
        else:
            console.print("Use: template new")
    else:
        parser.print_help()