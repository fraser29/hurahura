# Contributing to hurahura

## Development Setup

### Makefiles

This project uses two Makefiles for streamlined development:

- **Top-level `Makefile`**: Project-wide convenience commands
- **`docs/Makefile`**: Sphinx documentation build system

### Common Commands

```bash
# Build documentation
make docs

# Clean documentation build
make docs-clean

# Serve documentation locally
make docs-serve

# Show all available commands
make help
```

## Documentation

The documentation is built using Sphinx. The top-level Makefile provides convenient wrappers around the Sphinx build commands in `docs/Makefile`.

## Testing

Run tests from the project root:

```bash
python -m pytest hurahura/tests/
```
