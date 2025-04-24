# Contributing to AIAI CLI

Thank you for your interest in contributing to AIAI CLI! This guide will help you get started with developing and improving the project.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- pip (Python package manager)

### Setup

1. Fork the repository on GitHub
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/aiai-cli.git
   ```
3. Set up a virtual environment:
   ```bash
   cd aiai-cli
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
5. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=aiai
```

### Code Style

We use `black`, `ruff`, and `mypy` for code formatting and linting. Pre-commit hooks will automatically check your code when committing.

You can also run these tools manually:

```bash
# Format code with black
black aiai tests

# Run ruff linter
ruff aiai tests

# Run type checking with mypy
mypy aiai
```

### Making Changes

1. Create a new branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes to the codebase
3. Write tests for your changes
4. Run tests to ensure they pass
5. Commit your changes
6. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
7. Open a pull request on GitHub

## Pull Request Guidelines

When submitting a pull request:

1. Ensure all tests pass
2. Update documentation for any changed functionality
3. Add a clear description of the changes
4. Reference any related issues
5. Follow the existing code style

## Documentation

The documentation is built with MkDocs. To run the documentation locally:

```bash
# Install MkDocs
pip install mkdocs

# Serve the documentation
mkdocs serve
```

Then open http://127.0.0.1:8000/ in your browser.

To build the documentation:

```bash
mkdocs build
```

This will create a `site` directory with the static HTML files.

## Project Structure

- `aiai/` - The main package
  - `app/` - Django app for storing and retrieving data
  - `cli/` - Command line interface
  - `code_analyzer/` - Code analysis tools
  - `optimizer/` - Optimization logic
  - `runner/` - Agent execution tools
  - `synthesizer/` - Synthetic data generation

## Getting Help

If you need help or have questions:

- Open an issue on GitHub
- Contact the maintainers at [email or other contact method]

## Thank You

Your contributions are greatly appreciated! Every contribution, no matter how small, helps make AIAI CLI better. 