# User Guide Overview

This user guide provides comprehensive information about using AIAI CLI to optimize AI agents.

## What is AIAI CLI?

AIAI CLI is a command-line tool designed to analyze and optimize AI agents. It uses advanced techniques to extract optimization rules from agent execution traces and provides actionable recommendations to improve performance, efficiency, and reliability.

## Core Components

The AIAI CLI system consists of several components working together:

### Code Analyzer

The Code Analyzer examines your agent's source code to build a dependency graph and understand the structure of your code. This information is used to identify potential optimization targets.

### Synthesizer

The Synthesizer generates synthetic data examples to test your agent. This ensures a diverse set of test cases to thoroughly exercise your agent's functionality.

### Runner

The Runner executes your agent with different inputs to capture execution traces. These traces provide valuable information about how your agent behaves under various conditions.


### Rule Extractor

The Rule Extractor analyzes execution traces to identify patterns and extract optimization rules.

### Rule Locator

The Rule Locator determines the specific locations in your code where optimization rules should be applied. It provides file paths, target functions or code sections.

## Workflow

The typical workflow for using AIAI CLI is:

1. **Setup**: Prepare your agent code and environment
2. **Analysis**: Run AIAI CLI to analyze your agent
3. **Evaluation**: Review the generated optimization report
4. **Implementation**: Apply the recommended optimizations to your code
5. **Verification**: Re-run your agent to verify improvements

## Next Steps
- See [examples](../examples/demo-email-agent.md) of AIAI CLI in action
