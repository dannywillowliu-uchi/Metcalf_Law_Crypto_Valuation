# Contributing

## Setup

```bash
git clone https://github.com/username/network-effects-analyzer.git
cd network-effects-analyzer
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pytest tests/
```

## Code Style

```bash
black src/ tests/
isort src/ tests/
flake8 src/ tests/
```

## Tests

```bash
pytest tests/ --cov=src
```

## Pull Requests

1. Branch from `main`
2. Add tests for new features
3. Ensure tests pass
4. Submit PR with clear description

## Adding Networks

1. Create collector in `src/data_collection/`
2. Add Dune query if needed
3. Add tests
4. Update README

## License

Contributions are MIT licensed.
