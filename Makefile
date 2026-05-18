.PHONY: install test lint demo tender-demo clean help

install: ## Install core SDK with dev dependencies
	cd packages/core && pip install -e ".[dev]"

test: ## Run test suite
	cd packages/core && pytest -v

test-cov: ## Run tests with coverage report
	cd packages/core && pytest -v --cov=agent_company --cov-report=term-missing

lint: ## Run linter (ruff)
	cd packages/core && ruff check src/

lint-fix: ## Run linter and auto-fix
	cd packages/core && ruff check --fix src/

demo: ## Run quickstart demo
	python examples/quickstart.py

tender-demo: ## Run full tender demo
	python examples/full_tender_demo.py

live-demo: ## Run live demo with mock LLM
	python examples/live_demo.py --mock

clean: ## Remove build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
