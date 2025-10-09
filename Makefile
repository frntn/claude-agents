UV ?= uv
PYTHON ?= python

.PHONY: help setup test test-azure-fsi test-azure-fsi-templates test-azure-fsi-squad test-all

help:
	@echo "Claude Agents task shortcuts:"
	@echo "  setup                    - Run environment bootstrap script"
	@echo "  test                     - Execute repository pytest suite"
	@echo "  test-azure-fsi           - Run all Azure FSI Landing Zone checks"
	@echo "  test-azure-fsi-templates - Validate AVM template generation (uses Azure CLI)"
	@echo "  test-azure-fsi-squad     - Smoke-test squad mode orchestration script"
	@echo "  test-all                 - Run pytest suite and Azure FSI checks"

setup:
	./scripts/setup.sh

test:
	$(UV) run pytest tests/

test-azure-fsi: test-azure-fsi-templates test-azure-fsi-squad

test-azure-fsi-templates:
	$(UV) run $(PYTHON) agents/azure-fsi-landingzone/test_avm_templates.py

test-azure-fsi-squad:
	$(UV) run $(PYTHON) agents/azure-fsi-landingzone/test_squad_mode.py

test-all: test test-azure-fsi
