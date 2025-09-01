# Top-level Makefile for hurahura project
#

.PHONY: help docs docs-clean docs-serve

help:
	@echo "Available targets:"
	@echo "  docs        - Build documentation"
	@echo "  docs-clean  - Clean documentation build"
	@echo "  docs-serve  - Serve documentation locally"
	@echo "  help        - Show this help message"

docs:
	@echo "Building documentation..."
	cd docs && make html

docs-clean:
	@echo "Cleaning documentation build..."
	cd docs && make clean

docs-serve:
	@echo "Serving documentation at http://localhost:8000"
	cd docs && python -m http.server 8000 --directory build/html
