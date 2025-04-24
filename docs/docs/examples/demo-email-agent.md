# Demo Email Agent Example

AIAI CLI includes a built-in demo email agent that you can use to explore its optimization capabilities. This page explains how to use the demo agent and what you can learn from it.

## What is the Demo Email Agent?

The demo email agent is a simple AI agent that:

1. Reads email messages
2. Categorizes them by priority and type
3. Generates appropriate responses
4. Tracks action items and follow-ups

It serves as a practical example of how AIAI CLI can identify optimization opportunities in real-world agent code.

## Running the Demo Agent Optimization

To optimize the demo email agent:

```bash
# Run AIAI CLI
aiai

# When prompted, select option 1 to optimize the built-in demo email agent
```

The CLI will guide you through the process with prompts. You'll need an OpenAI API key, which you can set in your `.env` file:

```bash
OPENAI_API_KEY=sk-your-api-key
```

## What to Expect

After running the optimization, you'll see a report with specific recommendations. For the demo agent, these typically include:

1. **Caching Optimizations**: The demo agent makes redundant API calls that could be cached
2. **Parallelization Opportunities**: Some operations could be executed concurrently
3. **Error Handling Improvements**: Places where error handling could be more robust
4. **Cost Reduction Strategies**: Ways to reduce the number of API calls or token usage

## Example Optimization Report

Here's a sample of what the optimization report might look like:

```markdown
# Final discovered optimization rule placements

| # | File | Target | Confidence | Rule |
| --- | --- | --- | --- | --- |
| 1 | examples/crewai/email_agent.py | process_email_batch | 92 | Always cache the results of categorize_email when processing multiple emails with similar content. |
| 2 | examples/crewai/email_agent.py | generate_response | 87 | Never make sequential API calls for sentiment analysis and response generation when they can be parallelized. |
| 3 | examples/crewai/email_agent.py | extract_action_items | 79 | Consider implementing a retry mechanism with exponential backoff for action item extraction to handle API rate limits. |
```

## Learning from the Demo

The demo agent is designed to showcase common inefficiencies in AI agent code. By studying the optimizations AIAI CLI recommends, you can:

1. Learn patterns to avoid in your own agent code
2. Understand how to structure your agents for better performance
3. See real examples of optimization rules in action
4. Get familiar with the AIAI CLI workflow before applying it to your own agents

## Next Steps

After exploring the demo agent:

1. Review the [optimization concepts](../concepts/agent-optimization.md) to understand the recommendations better
2. Try optimizing [your own agent](custom-agents.md) with AIAI CLI
3. Learn more about [configuration options](../user-guide/configuration.md) to customize the optimization process 