#!/bin/bash

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Build MkDocs site
mkdocs build

# Verify site was built
echo "Build completed, contents of site directory:"
ls -la site/ 