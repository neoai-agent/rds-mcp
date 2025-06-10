.PHONY: clean build test upload install-dev help format lint bump-patch bump-minor bump-major

# Variables
PYTHON := python3
PACKAGE_NAME := rds-mcp
VERSION := $(shell grep 'version=' setup.py | cut -d"'" -f2)

help:
	@echo "Available commands:"
	@echo "  make clean        - Remove build artifacts and cache files"
	@echo "  make build        - Build the package"
	@echo "  make test         - Run tests"
	@echo "  make upload       - Upload to PyPI"
	@echo "  make install-dev  - Install development dependencies"
	@echo "  make format       - Format code using black and isort"
	@echo "  make lint         - Run linting checks"
	@echo "  make bump-patch   - Bump patch version"
	@echo "  make bump-minor   - Bump minor version"
	@echo "  make bump-major   - Bump major version"
	@echo "  make all          - Clean, build, test, and upload"

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +

build: clean
	$(PYTHON) -m pip install --upgrade build
	$(PYTHON) -m build
	@echo "Built package version $(VERSION)"

test:
	$(PYTHON) -m pytest tests/ -v

upload: build
	$(PYTHON) -m pip install --upgrade twine
	$(PYTHON) -m twine check dist/*
	@echo "Uploading version $(VERSION) to PyPI..."
	$(PYTHON) -m twine upload dist/*

install-dev:
	$(PYTHON) -m pip install -e ".[dev]"

all: clean build test upload

# Development helpers
format:
	$(PYTHON) -m pip install black isort
	black .
	isort .

lint:
	$(PYTHON) -m pip install ruff
	ruff check .
	ruff format --check .

# Version management
bump-patch:
	@echo "Bumping patch version..."
	@sed -i '' 's/version=".*"/version="$(shell echo $(VERSION) | awk -F. '{print $$1"."$$2"."$$3+1}')"/' setup.py
	@sed -i '' 's/__version__ = ".*"/__version__ = "$(shell echo $(VERSION) | awk -F. '{print $$1"."$$2"."$$3+1}')"/' rds_mcp/__init__.py

bump-minor:
	@echo "Bumping minor version..."
	@sed -i '' 's/version=".*"/version="$(shell echo $(VERSION) | awk -F. '{print $$1"."$$2+1".0"}')"/' setup.py
	@sed -i '' 's/__version__ = ".*"/__version__ = "$(shell echo $(VERSION) | awk -F. '{print $$1"."$$2+1".0"}')"/' rds_mcp/__init__.py

bump-major:
	@echo "Bumping major version..."
	@sed -i '' 's/version=".*"/version="$(shell echo $(VERSION) | awk -F. '{print $$1+1".0.0"}')"/' setup.py
	@sed -i '' 's/__version__ = ".*"/__version__ = "$(shell echo $(VERSION) | awk -F. '{print $$1+1".0.0"}')"/' rds_mcp/__init__.py 