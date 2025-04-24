# Optimizing Custom Agents

This guide explains how to use AIAI CLI to optimize your own custom AI agents. While the [demo agent](demo-email-agent.md) is useful for learning, the real power of AIAI CLI comes from optimizing your own agent code.

## Prerequisites

Before optimizing your custom agent, ensure:

1. Your agent has a main entry point file 
2. The entry point file has a `main(inputs=None)` function that runs your agent with the provided inputs (the `inputs` parameter is optional)
3. [AIAI CLI is installed](../getting-started/getting-started.md) and configured

## Creating an Entrypoint File

AIAI CLI requires a specific entrypoint file structure to interact with your agent. This file must:

1. Have a `main(inputs=None)` function that accepts an optional input example
2. Run your agent with the provided inputs
3. Return the agent's output

Here's what a minimal entrypoint file should look like:

```python
# entrypoint.py
def main(inputs=None):
    # Initialize your agent
    agent = get_your_agent()
    
    # Use the provided inputs or a default one
    inputs = inputs or "Default inputs input here"
    
    # Run your agent with the inputs
    result = agent.run(inputs)  # Or however your agent accepts inputs
    
    # Return the result
    return result
```

AIAI CLI will call this `main()` function with different synthetic examples during optimization.

## Preparing Your Agent

To prepare your agent for optimization:

1. **Document Dependencies**: Ensure all dependencies are properly installed
2. **Test Your Agent**: Make sure your agent runs correctly before optimization

## Running the Optimization

To optimize your custom agent:

```bash
# Run AIAI CLI
aiai

# When prompted, select option 2 to optimize your own agent
```

When prompted, provide the path to your agent's entry point file. AIAI CLI will:

1. Validate your entrypoint file
2. Analyze your agent's code 
3. Generate synthetic test data
4. Run your agent with multiple examples
5. Extract optimization rules
6. Generate a comprehensive report
