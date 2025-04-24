# AIAI CLI

AIAI CLI is a powerful tool designed to optimize AI agents through rule extraction and automated analysis. It helps identify optimization opportunities in your agent code and provides actionable recommendations based on execution traces.

## Key Features

- **Agent Optimization**: Automatically analyze your agent code to identify optimization opportunities
- **Synthetic Data Generation**: Generate diverse test cases to thoroughly exercise your agent
- **Built-in Demo**: Includes a demo email agent for experimentation and learning
- **Comprehensive Analysis**: Detailed reports with actionable recommendations and confidence scores
- **Evaluation Framework**: Includes both rule-based evaluation and head-to-head comparative evaluation for agent outputs

## Getting Started

One-liner to play with the demo email agent:

```bash
OPENAI_API_KEY='sk-...' uvx --from 'aiai-cli[crewai]' aiai
```

Get up and running quickly with AIAI CLI:

```bash
# Install the AIAI CLI tool
pip install aiai-cli
uv add aiai-cli

# Run AIAI CLI
aiai
```

For detailed installation instructions and usage guide, visit the [Getting Started](getting-started/getting-started.md) page.

## Why AIAI CLI?

AIAI CLI helps you improve the efficiency, reliability, and performance of your AI agents by:

1. Analyzing execution patterns across multiple runs
2. Identifying bottlenecks and optimization opportunities
3. Providing concrete, actionable recommendations
4. Generating comprehensive optimization reports
5. Mapping optimization rules to specific locations in your code
6. Quantitatively evaluating agent outputs against defined criteria

Learn more about the [concepts behind AIAI CLI](concepts/rule-extraction.md) and how it can help optimize your agents.
