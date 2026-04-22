.DEFAULT_GOAL := help

.PHONY: help test lint

help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^## / { printf "\n\033[1m%s\033[0m\n", substr($$0, 4) } ' $(MAKEFILE_LIST)

test: ## Run all tests
	uv run pytest -v

lint: ## Lint and type check
	uv run ruff check .
	uv run ruff format --check .
	uv run ty check
