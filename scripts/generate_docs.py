import os
import json
import re

def generate_docs(templates_dir="templates"):
    output = ["# Available Templates\n"]
    output.append("| Name | Type | Status | Parameters |")
    output.append("|---|---|---|---|")
    
    for filename in sorted(os.listdir(templates_dir)):
        if not filename.endswith('.json'):
            continue
            
        name = filename.replace('.json', '')
        path = os.path.join(templates_dir, filename)
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        node_type = "unknown"
        meta_info = {}
        try:
            data = json.loads(content)
            node_type = data.get("type", "unknown")
            meta_info = data.get("_meta", {})
        except json.JSONDecodeError:
            type_match = re.search(r'"type":\s*"([^"]+)"', content)
            if type_match:
                node_type = type_match.group(1)
            
        params = set(re.findall(r'{{{\s*([a-zA-Z0-9_]+)', content))
        params = {p for p in params if p not in ["loop", "item", "default"]}
        
        # Improvement #16: Enhanced Docs
        status = []
        if meta_info.get("deprecated"):
            status.append("[Deprecated]")
        
        required = meta_info.get("required_params", [])
        
        # Format params
        formatted_params = []
        for p in sorted(params):
            if p in required:
                formatted_params.append(f"**{p}**")
            else:
                formatted_params.append(p)
                
        status_str = ", ".join(status) if status else "Active"
        
        output.append(f"| `{name}` | `{node_type}` | {status_str} | {', '.join(formatted_params)} |")
        
    with open("TEMPLATES.md", "w", encoding='utf-8') as f:
        f.write("\n".join(output))
    
    print("Generated TEMPLATES.md")

if __name__ == "__main__":
    generate_docs()
