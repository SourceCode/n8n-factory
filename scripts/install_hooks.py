import os

HOOK_CONTENT = """#!/bin/sh
echo "Running n8n-factory tests..."
python -m pytest tests/
if [ $? -ne 0 ]; then
    echo "Tests failed! Aborting commit."
    exit 1
fi
"""

def install_hook():
    hooks_dir = ".git/hooks"
    if not os.path.exists(hooks_dir):
        print("Not a git repository (or .git/hooks missing). Skipping hook installation.")
        return

    hook_path = os.path.join(hooks_dir, "pre-commit")
    with open(hook_path, "w") as f:
        f.write(HOOK_CONTENT)
    
    # Make executable (Windows doesn't really care about chmod for git hooks usually run by bash, 
    # but good practice for *nix compatibility)
    # os.chmod(hook_path, 0o755) 
    print(f"Installed pre-commit hook at {hook_path}")

if __name__ == "__main__":
    install_hook()
