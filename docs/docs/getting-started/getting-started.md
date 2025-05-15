# Getting Started

To get started using AIAI CLI:

1. Install AIAI CLI from PyPI with:

   ```bash
   pip install aiai-cli
   # Or use uv, rye, etc.
   uv add aiai-cli
   ```

## Setting Up Your Environment

AIAI CLI requires an OpenAI API key for all core functionality, including code analysis, rule extraction, optimization, and rule localization.

Set your OpenAI API key in your shell environment:

```bash
export OPENAI_API_KEY=sk-your-api-key
```

## System Requirements

- Python 3.11 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## Understanding AIAI CLI

AIAI CLI is designed to optimize AI agents through an interactive process:

1. **Code Analysis** - AIAI analyzes your agent's code to build a dependency graph
2. **Evaluation Generation** - The system creates evaluation criteria specific to your agent
3. **Synthetic Data** - Test examples are generated to evaluate performance
4. **Rule Extraction** - Optimization rules are extracted by analyzing execution traces
5. **Rule Localization** - The system identifies exactly where to apply optimizations

Each of these steps works together to improve your agent's performance and reliability.

## Running Your First Optimization

Let's get started with a simple optimization run:

### Demo Agent Optimization

The easiest way to start is with the built-in demo email agent:

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

Select option 1 and continue following the prompts:

```
🔑 The demo agent requires an OpenAI API key...
Have you added an `OPENAI_API_KEY` to the `.env` file? [y/N]:
```

After confirming, AIAI will start the optimization process:

```
✅ Validating entrypoint… completed in 0.52s
✅ Analyzing code… completed in 5.24s
The agent is designed to create personalized sales emails for potential leads...

✅ Generating evals… completed in 3.18s
✅ Generating 25 synthetic inputs… completed in 7.65s
✅ Evaluating... completed in 42.31s
✅ Optimizing… completed in 12.47s
✅ Generating code modifications… completed in 8.92s

📋 Optimization results:

# /path/to/crewai_agent.py

ALWAYS
Limit the email to 2–3 concise paragraphs
/path/to/crewai_agent.py:41
---
TIPS
Craft a concise, professional, and solution-oriented tone that is tailored to the recipient's industry and technical level
/path/to/crewai_agent.py:41
---
...

📝 Report saved to: optimization_20250513_0205.md
```

## Understanding the Results

After the optimization run completes, AIAI CLI generates a markdown report like this:

```markdown
# /path/to/crewai_agent.py

ALWAYS
Limit the email to 2–3 concise paragraphs
/path/to/crewai_agent.py:41
---
TIPS
Craft a concise, professional, and solution-oriented tone that is tailored to the recipient's industry and technical level
/path/to/crewai_agent.py:41
---
NEVER
Exceed the 2–3 paragraph limit
/path/to/crewai_agent.py:41
---
TIPS
Map Zenbase features and benefits directly to the recipient's specific pain points and business context
/path/to/crewai_agent.py:42
---
ALWAYS
Generate exactly one concise, personalized sales email per input lead
/path/to/crewai_agent.py:51
---
ALWAYS
Include a clear, direct call to action (CTA) in the final paragraph of the email
/path/to/crewai_agent.py:56
---
...
```

The report categorizes optimization rules into three types:

1. **ALWAYS** - Critical rules that should always be followed
2. **NEVER** - Anti-patterns to avoid in your agent
3. **TIPS** - Best practices to improve agent performance

Each rule includes the file path and line number where it should be applied.


### Optimizing Your Own Agent

Once you're familiar with the demo, you can optimize your own agent. For a detailed walkthrough of optimizing your custom agent, see the [Optimizing Your Own Agent](../examples/custom-agents.md) guide.

## Next Steps

- Learn more about [rule extraction](../concepts/rule-extraction.md)
- See examples of [custom agent optimization](../examples/custom-agents.md)
