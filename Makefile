.PHONY: setup format lint test clean install db-init db-migrate run dev-run

# Development setup
setup:
	pip install -e ".[dev]"
	pre-commit install

# Format code
format:
	black .
	isort .

# Lint code
lint:
	flake8 .
	@echo "Skipping mypy due to package naming issue"
	black --check .
	isort --check .

# Run tests
test:
	pytest

# Clean temporary files
clean:
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

# Install in production mode
install:
	pip install .

# Initialize database
db-init:
	python -c "import asyncio; from utils.database import init_database; asyncio.run(init_database())"

# Create a new migration
db-migrate:
	alembic revision --autogenerate -m "$(message)"

# Apply migrations
db-upgrade:
	alembic upgrade head

# Run the bot
run:
	python main.py

# Run in development mode with hot reload
dev-run:
	watchmedo auto-restart --pattern="*.py" --recursive -- python main.py
