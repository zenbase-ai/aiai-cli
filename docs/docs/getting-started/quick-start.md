# Quick Start Guide

This guide will help you get started with AIAI CLI by running your first optimization.

## Prerequisites

- [AIAI CLI installed](installation.md)
- OpenAI API key (for the demo agent)

## Running the Demo Agent

AIAI CLI comes with a built-in demo email agent that you can use to explore the optimization capabilities:

```bash
# Run the AIAI CLI
aiai

# When prompted, select option 1 to optimize the built-in demo email agent
```

The CLI will guide you through the process with prompts:

1. You'll be asked to confirm access to your OpenAI API key
2. The system will validate the demo agent's entrypoint
3. Code analysis will be performed to build a dependency graph
4. Evaluation criteria will be generated
5. Synthetic data will be created
6. The optimization run will analyze and extract rules
7. Finally, a report will be generated with optimization recommendations

## Optimizing Your Own Agent

To optimize your own agent:

```bash
# Run the AIAI CLI
aiai

# When prompted, select option 2 to optimize your own agent
```

You'll be asked to provide the path to your agent's entrypoint file. This file must have a `main()` function that runs your agent.

Follow the interactive prompts to complete the optimization process.

## Understanding the Results

After the optimization run completes, AIAI CLI generates a markdown report in your current directory (e.g., `optimizations_report_20250423_2132.md`). This report contains:

- File paths where optimizations can be applied
- Target code sections or functions
- Confidence scores for each recommendation
- Detailed rule text describing the recommended optimization

## Next Steps

- Learn more about [rule extraction](../concepts/rule-extraction.md)
- Explore [configuration options](../user-guide/configuration.md)
- See examples of [custom agent optimization](../examples/custom-agents.md) 