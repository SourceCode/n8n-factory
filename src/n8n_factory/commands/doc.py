from rich.console import Console
from ..models import Recipe
import json

console = Console()

def doc_command(recipe: Recipe, json_output: bool = False, prompt_mode: bool = False):
    if prompt_mode:
        md = "Create an n8n workflow with the following logic:\n\n"
        for i, step in enumerate(recipe.steps):
            md += f"{i+1}. Use a **{step.template}** node named '{step.id}'."
            if step.description:
                md += f" Purpose: {step.description}."
            if step.params:
                md += f" Configure it with: {json.dumps(step.params)}."
            md += "\n"
        if recipe.tags:
            md += f"\nTags: {', '.join(recipe.tags)}"
            
    else:
        md = f"# {recipe.name}\n\n"
        if recipe.description:
            md += f"{recipe.description}\n\n"
        
        md += "## Workflow Steps\n\n"
        for i, step in enumerate(recipe.steps):
            icon = "🔹"
            if "webhook" in step.template or "trigger" in step.template.lower(): icon = "⚡"
            elif "if" in step.template or "switch" in step.template: icon = "🔀"
            elif "set" in step.template: icon = "📝"
            
            md += f"### {i+1}. {icon} {step.id}\n"
            md += f"- **Template**: `{step.template}`\n"
            
            if step.description:
                 md += f"- **Description**: {step.description}\n"
            if step.notes:
                md += f"\n> {step.notes}\n\n"
            else:
                md += "\n"
            
    if json_output:
        print(json.dumps({"markdown": md, "mode": "prompt" if prompt_mode else "doc"}, indent=2))
    else:
        print(md)