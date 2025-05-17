# Lead Email Generation Example

This example demonstrates how to use CrewAI to extract lead information from unstructured text and generate personalized sales emails.

## Installation

This example requires the CrewAI optional feature to be installed. You can install it using:

```bash
# Using rye
rye sync --features crewai

# Using pip
pip install -e ".[crewai]"
```

## API Keys

This example uses OpenAI's models by default and requires you to set up your API key:

1. Use the provided `.env` file in the `src/aiai/examples/crewai/` directory
2. Add your OpenAI API key: `OPENAI_API_KEY=your_api_key_here`

You can also place the `.env` file in your project root directory, or set the environment variable directly:

```bash
# Linux/macOS
export OPENAI_API_KEY=your_api_key_here

# Windows
set OPENAI_API_KEY=your_api_key_here
```

## Overview

The crew consists of two AI agents:
1. **Lead Profile Extractor** - Parses unstructured text to extract structured lead information
2. **Email Crafter** - Creates personalized sales emails based on the extracted lead profiles

## File Structure

- `crew.py` - Contains the main `LeadEmailCrew` class with agent and task definitions
- `entrypoint.py` - Simple execution script that runs the crew

## How to Run

The simplest way to run the example is:

```bash
# From project root
rye run python -m aiai.examples.crewai.entrypoint
```

## Input Data

The crew reads lead data from a `people_data.json` file with the following structure:

```json
{
  "leads_text": "Unstructured text containing information about multiple leads..."
}
```

The entrypoint.py file will automatically create a sample people_data.json file if one doesn't exist.

## Output

The script will output structured lead profiles followed by personalized sales emails for each lead.