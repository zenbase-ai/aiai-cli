# AIAI Project Structure Overview

This document provides an overview of the AIAI project's directory structure and the purpose of each component.

## Directory Structure

```
aiai/
├── __init__.py             # Package initialization file
├── app/                    # Web application components
│   ├── __init__.py
│   ├── apps.py
│   ├── migrations/         # Database migration files
│   ├── models.py           # Data models definition
│   ├── settings.py         # Application configuration
│   └── tests.py            # App tests
├── code_analyzer/          # Code analysis functionality
│   ├── __init__.py
│   ├── analyzer.py         # Core analysis logic
│   ├── graph.py            # Graph representation of code
│   ├── parsers/            # Code parsing components
│   ├── readme.md           # Documentation for code analyzer
│   └── tests/              # Test suite for analyzer
├── examples/               # Example code and use cases
├── llm_context/            # LLM contextual information
│   └── overview.md         # This file - project structure overview
├── logger/                 # Logging system
│   ├── __init__.py
│   ├── extractor.py        # Log data extraction
│   ├── log_ingestor.py     # Log ingestion functionality
│   ├── openlit_exporters.py # Log export functionality
│   └── test_logger.py      # Logger test suite
├── main.py                 # Main application entry point
├── manage.py               # Project management script
├── prompt_finder.py        # Utility for finding prompts
└── utils.py                # General utility functions
```

## Component Descriptions

### App
The `app` directory contains web application components, potentially using a framework like Django. It includes models, settings, and migrations for database management.

### Code Analyzer
The `code_analyzer` directory provides functionality for analyzing code. It includes:
- `analyzer.py`: Core analysis logic
- `graph.py`: Graph-based representation of code structure
- `parsers/`: Components for parsing different types of code
- Comprehensive test suite and documentation

### Examples
Contains example code and use cases demonstrating the functionality of the AIAI system.

### LLM Context
The `llm_context` directory stores contextual information for Large Language Models to understand the project structure and functionality.

### Logger
The `logger` directory implements a logging system with:
- `log_ingestor.py`: For ingesting and processing logs
- `extractor.py`: For extracting data from logs
- `openlit_exporters.py`: For exporting logs to external systems
- Test suite for validation

### Core Files
- `main.py`: The main entry point for the AIAI application
- `manage.py`: Project management script for administrative tasks for Django
- `utils.py`: General utility functions used across the project