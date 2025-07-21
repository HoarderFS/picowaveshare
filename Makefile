# Makefile for Waveshare Pico Relay B Project

# Variables
PYTHON := python3
VENV := venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip
MICROPYTHON_DIR := micropython
PYTHON_DIR := python
TESTS_DIR := $(PYTHON_DIR)/tests
# Use environment variable for PICO_PORT, with a default value
PICO_PORT ?= /dev/cu.usbmodem84401

# Default target
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  setup           - Set up development environment"
	@echo "  install         - Install dependencies"
	@echo "  lint            - Run code linting with ruff"
	@echo "  format          - Format code with ruff and black"
	@echo "  test            - Run tests with pytest (mocked)"
	@echo "  test-hardware   - Run tests with real hardware"
	@echo "  coverage        - Run tests with coverage report (mocked)"
	@echo "  coverage-hardware - Run hardware tests with coverage"
	@echo "  clean           - Clean up generated files"
	@echo "  hardware        - Run old hardware verification scripts"
	@echo "  deploy          - Deploy MicroPython code to Pico"
	@echo "  all             - Run lint, test, and coverage"

# Setup development environment
.PHONY: setup
setup: $(VENV)/bin/activate
	$(VENV_PIP) install -r requirements-dev.txt
	@echo "Development environment set up successfully!"

# Create virtual environment
$(VENV)/bin/activate:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PIP) install --upgrade pip

# Install dependencies
.PHONY: install
install: $(VENV)/bin/activate
	$(VENV_PIP) install -r requirements-dev.txt

# Lint code
.PHONY: lint
lint: $(VENV)/bin/activate
	$(VENV_PYTHON) -m ruff check .
	@echo "Linting completed!"

# Format code
.PHONY: format
format: $(VENV)/bin/activate
	$(VENV_PYTHON) -m ruff format .
	$(VENV_PYTHON) -m black .
	@echo "Code formatting completed!"

# Run tests
.PHONY: test
test: $(VENV)/bin/activate
	$(VENV_PYTHON) -m pytest $(TESTS_DIR) -v

# Run tests with coverage
.PHONY: coverage
coverage: $(VENV)/bin/activate
	$(VENV_PYTHON) -m pytest $(TESTS_DIR) --cov=waveshare_relay --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/"

# Run tests with real hardware
.PHONY: test-hardware
test-hardware: $(VENV)/bin/activate
	@echo "Running tests with real hardware..."
	HARDWARE_TEST=true $(VENV_PYTHON) -m pytest $(TESTS_DIR) -v -s
	@echo "Hardware tests completed!"

# Run hardware tests with coverage
.PHONY: coverage-hardware
coverage-hardware: $(VENV)/bin/activate
	@echo "Running hardware tests with coverage..."
	HARDWARE_TEST=true $(VENV_PYTHON) -m pytest $(TESTS_DIR) --cov=waveshare_relay --cov-report=html --cov-report=term-missing -v -s
	@echo "Hardware coverage report generated in htmlcov/"

# Clean up generated files
.PHONY: clean
clean:
	rm -rf $(VENV)
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +
	@echo "Cleaned up generated files!"

# Hardware tests (requires connected Pico)
.PHONY: hardware
hardware: $(VENV)/bin/activate
	@echo "Running hardware tests..."
	@echo "Checking for available ports:"
	@ls /dev/cu.usbmodem* 2>/dev/null || echo "No usbmodem ports found"
	@echo "Running hardware verification tests..."
	$(VENV_PYTHON) tests/hardware_verification/verify_connection.py
	$(VENV_PYTHON) tests/hardware_verification/test_protocol.py

# Deploy MicroPython code to Pico
.PHONY: deploy
deploy: $(VENV)/bin/activate
	@echo "Deploying MicroPython code to Pico..."
	@if [ -e "$(PICO_PORT)" ]; then \
		$(VENV_PYTHON) -m mpremote connect $(PICO_PORT) cp $(MICROPYTHON_DIR)/main.py :; \
		$(VENV_PYTHON) -m mpremote connect $(PICO_PORT) cp $(MICROPYTHON_DIR)/config.py :; \
		$(VENV_PYTHON) -m mpremote connect $(PICO_PORT) cp $(MICROPYTHON_DIR)/relay_controller.py :; \
		$(VENV_PYTHON) -m mpremote connect $(PICO_PORT) cp $(MICROPYTHON_DIR)/protocol.py :; \
		echo "Deployment completed!"; \
	else \
		echo "Error: Pico not found at $(PICO_PORT)"; \
		exit 1; \
	fi

# Run all quality checks
.PHONY: all
all: lint test coverage
	@echo "All quality checks completed!"

# Development workflow
.PHONY: dev
dev: format lint test
	@echo "Development workflow completed!"

# Check if virtual environment exists
.PHONY: check-venv
check-venv:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Virtual environment not found. Run 'make setup' first."; \
		exit 1; \
	fi