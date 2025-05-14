# Getting Started with AIAI CLI

This guide will help you install AIAI CLI and run your first agent optimization.

## Installation

### System Requirements

- Python 3.11 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Installation Steps

1. **Install AIAI CLI**

   ```bash
   # Install from PyPI
   pip install aiai-cli
   # Or use uv, rye, etc.
   uv add aiai-cli
   ```

2. **Set Up Your OpenAI API Key**

   AIAI CLI requires an OpenAI API key for all core functionality, including code analysis, rule extraction, optimization, and rule localization.

   Create a `.env` file in your project directory and add your OpenAI API key:

   ```bash
   OPENAI_API_KEY=sk-your-api-key
   ```

## Running Your First Optimization

AIAI CLI provides an interactive interface to optimize AI agents. Let's get started with a simple optimization run.

### Demo Agent Optimization

The easiest way to get started is to use the built-in demo email agent:

```bash
# Run AIAI CLI
aiai
# When prompted, select option 1 to optimize the built-in demo email agent
```

The CLI will guide you through the optimization process with prompts:

1. You'll be asked to confirm access to your OpenAI API key
2. The system will validate the demo agent's entrypoint
3. Code analysis will be performed to build a dependency graph
4. Evaluation criteria will be generated
5. Synthetic data will be created for testing
6. The optimization run will analyze execution traces and extract rules
7. Finally, a report will be generated with specific optimization recommendations

### Optimizing Your Own Agent

Once you're familiar with the demo, you can optimize your own agent:

```bash
# Run AIAI CLI
aiai
# When prompted, select option 2 to optimize your own agent
```

You'll be asked to provide the path to your agent's entrypoint file. This file must have a `main()` function that runs your agent.

Follow the interactive prompts to complete the optimization process.

## Understanding the Results

After the optimization run completes, AIAI CLI generates a markdown report in your current directory (e.g., `optimizations_report_20250423_2132.md`).

This report contains:

- **File paths**: Where optimizations can be applied
- **Target functions/sections**: Specific parts of code to modify
- **Rule descriptions**: Detailed explanations of the recommended optimizations

## Next Steps

- Learn more about [rule extraction](../concepts/rule-extraction.md)
- See examples of [custom agent optimization](../examples/custom-agents.md)
