.PHONY: install test lint format clean

install:
	pip install -e .

test:
	pytest tests/

lint:
	ruff check src/

format:
	ruff format src/

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache
