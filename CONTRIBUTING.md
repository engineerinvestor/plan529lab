# Contributing to plan529lab

Thank you for your interest in contributing.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/engineerinvestor/plan529lab.git
cd plan529lab

# Create a virtual environment (Python 3.11+)
python3 -m venv .venv
source .venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"
```

## Running Tests

All code must pass before submitting a PR:

```bash
# Tests
pytest -v

# Linting
ruff check .

# Type checking
mypy .
```

## Code Standards

- Type hints on all functions and methods
- Pydantic v2 models with `frozen=True` for domain objects
- Tax computation functions are pure (floats in, floats out) for testability
- New features need tests — unit tests at minimum, integration tests preferred

## Pull Request Process

1. Fork the repository and create a feature branch
2. Make your changes
3. Ensure `pytest`, `ruff check .`, and `mypy .` all pass
4. Write a clear PR description explaining what and why
5. Submit the PR

## Adding a State Rule

To add a new state-specific tax rule:

1. Create a new file in `plan529lab/state_rules/`
2. Subclass `StateRule` from `plan529lab/tax/state_base.py`
3. Implement `contribution_benefit()`, `recapture_tax()`, and `validate()`
4. Register it in `plan529lab/tax/state_registry.py`
5. Add tests in `tests/test_state_rules.py`
6. Document the state's specific rules and validation sources

## Important Note

This package models tax rules, not tax law. Any state-specific implementation must:
- Be validated against official state guidance
- Include a disclaimer that it's a model, not legal advice
- Document the source and date of the rules it encodes
