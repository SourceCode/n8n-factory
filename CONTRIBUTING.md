# Contributing to n8n-factory

Thank you for your interest in contributing to n8n-factory! We welcome contributions from everyone.

## Getting Started

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/username/n8n-factory.git
    cd n8n-factory
    ```

2.  **Install dependencies:**
    ```bash
    pip install -e .
    pip install -r requirements-dev.txt
    ```

## Development Workflow

*   **Code Style:** We follow PEP 8 standards. Please use `black` or `ruff` to format your code before submitting.
*   **Tests:** Run the test suite to ensure no regressions:
    ```bash
    pytest tests/
    ```
    We aim for high test coverage for all new features.
*   **Templates:**
    *   To add a new template, place the JSON file in the `templates/` directory.
    *   Ensure the filename matches the convention (snake_case).
    *   Run `python scripts/generate_docs.py` to update the documentation.

## Pull Requests

1.  Create a feature branch for your changes.
2.  Ensure all tests pass.
3.  Update `CHANGELOG.md` with a brief description of your changes.
4.  Submit a Pull Request with a clear description of the problem and solution.

## Community

We rely on the community to keep this project vibrant and useful. Please be respectful and follow our [Code of Conduct](CODE_OF_CONDUCT.md).