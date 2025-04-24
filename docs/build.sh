#!/bin/bash

# Print Python version and location
which python3 || which python
python3 --version || python --version

# Create and activate virtual environment
python3 -m venv venv || python -m venv venv
source venv/bin/activate

# Install Python dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Build MkDocs site
python -m mkdocs build

# Verify site was built
echo "Build completed, contents of site directory:"
ls -la site/ || echo "Site directory not found" 