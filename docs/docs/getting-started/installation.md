# Installation

This guide will help you install and set up the AIAI CLI tool.

## System Requirements

- Python 3.9 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## Installation Steps

### 1. Create a Virtual Environment (Recommended)

```bash
# Create a virtual environment
python -m venv aiai-env

# Activate the virtual environment
# On Linux/macOS
source aiai-env/bin/activate
# On Windows
aiai-env\Scripts\activate
```

### 2. Install AIAI CLI

```bash
# Install from PyPI
pip install aiai-cli

# Alternatively, install from source
git clone https://github.com/zenbase/aiai-cli.git
cd aiai-cli
pip install -e .
```

### 3. Verify Installation

Verify that AIAI CLI is installed correctly:

```bash
aiai --version
```

You should see the version number of the installed AIAI CLI.

## Environment Setup

AIAI CLI requires an OpenAI API key for some features, especially when using the built-in demo agent.

1. Create a `.env` file in your project directory
2. Add your OpenAI API key to the file:

```bash
OPENAI_API_KEY=sk-your-api-key
```

## Next Steps

Once installation is complete, proceed to the [Quick Start Guide](quick-start.md) to run your first optimization. 