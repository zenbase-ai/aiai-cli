# Optimizing Your Own Agent

This guide walks through the process of optimizing your own AI agent using the AIAI CLI.

## Prerequisites

Before optimizing your own agent, make sure you have:

1. AIAI CLI installed
2. Your OpenAI API key set in your environment:
   ```bash
   export OPENAI_API_KEY=sk-your-api-key
   ```
3. A Python agent with a proper entrypoint file

## Preparing Your Agent

AIAI CLI requires an entrypoint file that contains a `main()` function. This function should:

1. Accept an input example parameter
2. Run your agent with that input
3. Return the agent's raw output

Here's an example of a properly structured entrypoint file:

```python
def main(example=None):
    crew = get_crewai_agent()
    example = example or "default example"
    result = crew.kickoff({"input": example})
    return result.raw
```

Save this file in your project directory. It will be the starting point for the optimization process.

## Running the Optimization

Start the optimization process by running:

```bash
aiai
```

You'll see the following output and prompts:

```
🚀 Welcome to aiai! 🤖

What would you like to optimize?
(1) Outbound email agent (Demo)
(2) My own agent
Enter your choice (1 or 2):
```

Select option 2, and you'll be prompted for your agent's entrypoint:

```
To optimize your own agent, we need an entrypoint.py file.
This file must have a `def main(example=None)` function that
runs your agent with the provided example.

Path to entrypoint:
```

Enter the full path to your entrypoint file (e.g., `/path/to/your/agent.py`).

After providing the path, the optimization process begins:

```
✅ Validating entrypoint… completed in 0.47s
✅ Analyzing code… completed in 6.12s
The agent is designed to...

✅ Generating evals… completed in 3.45s
✅ Generating 25 synthetic inputs… completed in 8.21s
✅ Evaluating... completed in 38.76s
✅ Optimizing… completed in 14.32s
✅ Generating code modifications… completed in 9.15s

📋 Optimization results:
...

📝 Report saved to: optimization_20250513_0205.md
```

## Understanding the Optimization Report

The optimization report contains specific rules categorized as:

1. **ALWAYS** - Critical rules that should always be followed
2. **NEVER** - Anti-patterns to avoid in your agent
3. **TIPS** - Best practices to improve agent performance

Each rule includes the file path and line number where it should be applied.

Here's an example of what the report might look like:

```markdown
# /path/to/your/agent.py

ALWAYS
Validate user input before processing
/path/to/your/agent.py:28
---
NEVER
Ignore error conditions from API calls
/path/to/your/agent.py:42
---
TIPS
Structure your response with clear sections for better readability
/path/to/your/agent.py:65
---
...
```

## Applying the Optimizations

Review each suggestion in the optimization report and apply them to your agent's code. Focus on:

1. The **ALWAYS** rules first - these are critical for correct behavior
2. The **NEVER** rules next - these help avoid common pitfalls
3. The **TIPS** for general improvements

The line numbers provided help you locate exactly where each rule should be applied.

## Advanced Configuration

For more advanced optimization scenarios, you can use command-line parameters:

```bash
aiai --analyzer openai/o4-mini --evaluator openai/o4-mini --optimizer openai/gpt-4.1 --examples 15
```

This allows you to:
- Select specific models for different parts of the optimization pipeline
- Control the number of synthetic examples generated
- Specify custom evaluation files
- And more

Run `aiai --help` for a complete list of options.
