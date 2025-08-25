.NOTPARALLEL:

# Use system uv
UV_BIN:=uv
UV_VENV:=$(CURDIR)/.venv
UV_DEPS:=$(UV_VENV)/.deps

.PHONY: help
help: ## Show this help message
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Environment setup
$(UV_DEPS): pyproject.toml
	$(UV_BIN) sync
	@touch $@

.PHONY: env
env: $(UV_DEPS)  ## Install and configure Python environment

# Assembly targets
.PHONY: assemble-counter
assemble-counter: env  ## Assemble counter example to binary
	$(UV_BIN) run python simple_asm.py counter.punch

.PHONY: assemble-friendly
assemble-friendly: env  ## Assemble friendly example to binary
	$(UV_BIN) run python simple_asm.py friendly.punch

.PHONY: assemble-examples
assemble-examples: assemble-counter assemble-friendly  ## Assemble all example programs

# Format conversion targets
.PHONY: format-counter
format-counter: env  ## Convert counter example to punch card format
	$(UV_BIN) run python punch_card_formatter.py example_counter.asm counter.punch

.PHONY: format-friendly
format-friendly: env  ## Convert friendly example to punch card format
	$(UV_BIN) run python punch_card_formatter.py example_friendly.asm friendly.punch

.PHONY: format-examples
format-examples: format-counter format-friendly  ## Convert all examples to punch card format

# Emulator targets
.PHONY: run-counter
run-counter: env assemble-counter  ## Run counter program in emulator with trace
	$(UV_BIN) run python simple_6502_emulator.py --load counter.bin@2000 --start 2000 --trace --max-cycles 200

.PHONY: run-friendly
run-friendly: env assemble-friendly  ## Run friendly program in emulator with trace
	$(UV_BIN) run python simple_6502_emulator.py --load friendly.bin@2000 --start 2000 --trace --max-cycles 500

.PHONY: test-emulator
test-emulator: run-counter  ## Basic emulator functionality test

# Bootstrap testing targets
.PHONY: format-assembler
format-assembler: env  ## Convert assembler source to punch format
	$(UV_BIN) run python punch_card_formatter.py assembler_source.asm assembler_source.punch

.PHONY: assemble-assembler
assemble-assembler: env  ## Assemble the 6502 assembler itself
	$(UV_BIN) run python simple_asm.py assembler_source.punch

.PHONY: test-bootstrap
test-bootstrap: env assemble-assembler format-assembler  ## Test assembler bootstrapping
	@echo "Testing assembler self-assembly..."
	$(UV_BIN) run python simple_6502_emulator.py \
		--load assembler_source.bin@0000 \
		--load assembler_source.punch@2000 \
		--start 0200 \
		--trap 8000 \
		--dump 8000:CFFF:bootstrap-output.bin \
		--compare 8000:CFFF:assembler_source.bin

# Development targets
.PHONY: format
format: env  ## Format code with ruff
	$(UV_BIN) run ruff format *.py

.PHONY: lint
lint: env  ## Lint code with ruff
	$(UV_BIN) run ruff check *.py

.PHONY: test
test: env  ## Run pytest tests
	$(UV_BIN) run pytest

.PHONY: check
check: lint test  ## Run all checks

# Documentation targets
.PHONY: docs
docs:  ## View format documentation
	@echo "=== Assembly Format Documentation ==="
	@echo "Key features: Instructions, Data definitions, Relocation"
	@echo ""
	@echo "Data definition examples:"
	@echo '  "HELLO"     ; String literal'
	@echo '  #DEADBEEF   ; Hex data'
	@echo ""
	@echo "Relocation examples:"
	@echo '  !1E00       ; Set offset'
	@echo '  @0200       ; Set effective address'
	@echo ""
	@echo "See format_documentation.md for complete details"

# Utility targets
.PHONY: clean-outputs
clean-outputs:  ## Clean generated binary files
	rm -f *.bin bootstrap-output.bin

.PHONY: clean-punch
clean-punch:  ## Clean generated punch card files (keeps examples as fixtures)
	@echo "Punch card files are kept as test fixtures"
	@echo "Use 'make format-examples' to regenerate them"

.PHONY: clean
clean: clean-outputs  ## Clean generated files (not dependencies)
	rm -f *.bin bootstrap-output.bin

.PHONY: clean-all
clean-all:  ## Clean everything including uv environment
	rm -rf $(UV_VENV) *.bin bootstrap-output.bin

# Default target
.PHONY: all
all: format-examples assemble-examples test-emulator  ## Build and test everything
