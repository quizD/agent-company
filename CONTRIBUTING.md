# Contributing to Agent Company

Thanks for your interest in contributing! This guide will help you get started.

## Development Setup

```bash
# Clone the repo
git clone https://github.com/agent-company/agent-company.git
cd agent-company

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install core with dev dependencies
cd packages/core
pip install -e ".[dev]"
```

## Code Style

- **Formatter/Linter**: [Ruff](https://docs.astral.sh/ruff/) with line length 100
- **Type hints**: Required for all public APIs
- **Docstrings**: Google style, in Chinese (matching existing codebase)
- **Python**: 3.10+ (no `StrEnum`, use `(str, Enum)` instead)

Run the linter:

```bash
make lint
```

## Running Tests

```bash
make test

# Or with verbose output
cd packages/core && pytest -v
```

## Pull Request Process

1. **Fork** the repository
2. **Create a branch** from `main`: `git checkout -b feature/your-feature`
3. **Write tests** for new functionality
4. **Ensure CI passes**: `make lint && make test`
5. **Submit a PR** using the PR template

### PR Guidelines

- Keep PRs focused — one feature or fix per PR
- Update documentation if you change public APIs
- Add a CHANGELOG entry under `[Unreleased]`
- Reference related issues with `Closes #123`

## Reporting Issues

- **Bugs**: Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md)
- **Features**: Use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md)
- **Security**: See [SECURITY.md](SECURITY.md)

## Project Structure

```
packages/
├── core/           # Core SDK (pool, tender, performance, values, economy, health)
├── cli/            # Command-line tool (agent-co)
├── server/         # FastAPI REST API
└── dashboard/      # React Web UI
```

## License

By contributing, you agree that your contributions will be licensed under the [Apache License 2.0](LICENSE).
