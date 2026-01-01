# Makefile for Agent Core Framework
# Provides convenient commands for development, testing, and operations

.PHONY: help install install-langgraph install-dev install-pip
.PHONY: test test-unit test-integration test-contracts
.PHONY: lint format check type-check
.PHONY: docker-build docker-run docker-compose-up docker-clean
.PHONY: clean verify setup-config run-example
.PHONY: docs-serve docs-check-links

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python
POETRY := poetry
DOCKER_IMAGE := agent-core-framework
DOCKER_TAG := latest
CONFIG_DIR := config
EXAMPLES_DIR := examples

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

##@ Installation

install: ## Install dependencies using Poetry
	@echo "$(BLUE)Installing dependencies with Poetry...$(NC)"
	$(POETRY) install --no-interaction

install-langgraph: ## Install dependencies with LangGraph extras
	@echo "$(BLUE)Installing dependencies with LangGraph support...$(NC)"
	$(POETRY) install --no-interaction --extras langgraph

install-dev: ## Install dependencies including dev dependencies
	@echo "$(BLUE)Installing dependencies with dev tools...$(NC)"
	$(POETRY) install --no-interaction --with dev

install-pip: ## Install using pip (development mode)
	@echo "$(BLUE)Installing with pip in development mode...$(NC)"
	$(PYTHON) -m pip install -e .

##@ Testing

test: ## Run all tests
	@echo "$(BLUE)Running all tests...$(NC)"
	$(POETRY) run pytest

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	$(POETRY) run pytest tests/unit/

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	$(POETRY) run pytest tests/integration/

test-contracts: ## Run contract tests only
	@echo "$(BLUE)Running contract tests...$(NC)"
	$(POETRY) run pytest tests/contracts/

##@ Code Quality

lint: ## Run linter (ruff check)
	@echo "$(BLUE)Running linter...$(NC)"
	$(POETRY) run ruff check .

format: ## Format code (ruff format)
	@echo "$(BLUE)Formatting code...$(NC)"
	$(POETRY) run ruff format .

check: lint ## Run linter and formatter check (alias for lint)
	@echo "$(GREEN)Code quality checks passed!$(NC)"

type-check: ## Run type checking (if mypy is available)
	@echo "$(YELLOW)Type checking requires mypy to be installed$(NC)"
	@if $(POETRY) run which mypy > /dev/null 2>&1; then \
		$(POETRY) run mypy agent_core/; \
	else \
		echo "$(YELLOW)mypy not installed, skipping type check$(NC)"; \
	fi

##@ Docker

docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

docker-build-langgraph: ## Build Docker image with LangGraph support
	@echo "$(BLUE)Building Docker image with LangGraph...$(NC)"
	docker build --build-arg EXTRAS=langgraph -t $(DOCKER_IMAGE):langgraph .

docker-run: ## Run example in Docker container
	@echo "$(BLUE)Running example in Docker...$(NC)"
	@if [ ! -d "$(CONFIG_DIR)" ]; then \
		echo "$(YELLOW)Creating config directory...$(NC)"; \
		mkdir -p $(CONFIG_DIR); \
		cp $(EXAMPLES_DIR)/config/agent-core.yaml $(CONFIG_DIR)/ 2>/dev/null || true; \
	fi
	docker run --rm \
		-v "$(PWD)/$(CONFIG_DIR):/app/$(CONFIG_DIR):ro" \
		-v "$(PWD)/$(EXAMPLES_DIR):/app/$(EXAMPLES_DIR):ro" \
		$(DOCKER_IMAGE):$(DOCKER_TAG) \
		$(PYTHON) $(EXAMPLES_DIR)/minimal_example.py

docker-compose-up: ## Start Docker Compose services
	@echo "$(BLUE)Starting Docker Compose services...$(NC)"
	@if [ ! -d "$(CONFIG_DIR)" ]; then \
		echo "$(YELLOW)Creating config directory...$(NC)"; \
		mkdir -p $(CONFIG_DIR); \
		cp $(EXAMPLES_DIR)/config/agent-core.yaml $(CONFIG_DIR)/ 2>/dev/null || true; \
	fi
	docker-compose up

docker-compose-down: ## Stop Docker Compose services
	@echo "$(BLUE)Stopping Docker Compose services...$(NC)"
	docker-compose down

docker-clean: ## Remove Docker images and containers
	@echo "$(BLUE)Cleaning Docker artifacts...$(NC)"
	docker rmi $(DOCKER_IMAGE):$(DOCKER_TAG) $(DOCKER_IMAGE):langgraph 2>/dev/null || true
	docker-compose down --rmi local 2>/dev/null || true

##@ Quality of Life

clean: ## Clean build artifacts, cache, and temporary files
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -r {} + 2>/dev/null || true
	@echo "$(GREEN)Clean complete!$(NC)"

verify: ## Verify installation and basic imports
	@echo "$(BLUE)Verifying installation...$(NC)"
	@$(POETRY) run $(PYTHON) -c "from agent_core.runtime import Runtime; from agent_core.configuration.loader import load_config; print('$(GREEN)✓ Installation verified!$(NC)')" || \
		(echo "$(YELLOW)Installation verification failed. Run 'make install' first.$(NC)" && exit 1)

setup-config: ## Set up configuration directory with example config
	@echo "$(BLUE)Setting up configuration...$(NC)"
	@mkdir -p $(CONFIG_DIR)
	@if [ ! -f "$(CONFIG_DIR)/agent-core.yaml" ]; then \
		cp $(EXAMPLES_DIR)/config/agent-core.yaml $(CONFIG_DIR)/; \
		echo "$(GREEN)Configuration file created at $(CONFIG_DIR)/agent-core.yaml$(NC)"; \
	else \
		echo "$(YELLOW)Configuration file already exists at $(CONFIG_DIR)/agent-core.yaml$(NC)"; \
	fi

run-example: setup-config ## Run the minimal example
	@echo "$(BLUE)Running minimal example...$(NC)"
	$(POETRY) run $(PYTHON) $(EXAMPLES_DIR)/minimal_example.py

##@ Documentation

docs-serve: ## Serve documentation (requires mkdocs or similar)
	@echo "$(YELLOW)Documentation serving not configured.$(NC)"
	@echo "$(YELLOW)View documentation in docs/ directory or README.md$(NC)"

docs-check-links: ## Check documentation links (basic validation)
	@echo "$(BLUE)Checking documentation links...$(NC)"
	@echo "$(YELLOW)Link checking requires manual review or external tools$(NC)"
	@echo "$(BLUE)Checking for common link issues...$(NC)"
	@grep -r "\[.*\](" docs/ README.md examples/README.md 2>/dev/null | grep -v "http" | head -20 || true
	@echo "$(GREEN)Basic link check complete. Review output above for issues.$(NC)"

##@ Help

help: ## Display this help message
	@echo "$(BLUE)Agent Core Framework - Makefile Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Usage:$(NC) make [target]"
	@echo ""
	@echo "$(GREEN)Available targets:$(NC)"
	@awk 'BEGIN {FS = ":.*##"; printf ""} /^[a-zA-Z_-]+:.*?##/ { printf "  $(BLUE)%-25s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(GREEN)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

