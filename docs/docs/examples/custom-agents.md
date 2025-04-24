# Optimizing Custom Agents

This guide explains how to use AIAI CLI to optimize your own custom AI agents. While the [demo agent](demo-email-agent.md) is useful for learning, the real power of AIAI CLI comes from optimizing your own agent code.

## Prerequisites

Before optimizing your custom agent, ensure:

1. Your agent is implemented in Python
2. Your agent has a main entry point file
3. The entry point file has a `main()` function or equivalent
4. [AIAI CLI is installed](../getting-started/installation.md) and configured

## Preparing Your Agent

To prepare your agent for optimization:

1. **Document Dependencies**: Ensure all dependencies are properly installed
2. **Test Your Agent**: Make sure your agent runs correctly before optimization
3. **Create Test Inputs**: Prepare some example inputs if your agent requires them

## Running the Optimization

To optimize your custom agent:

```bash
# Run AIAI CLI
aiai

# When prompted, select option 2 to optimize your own agent
```

When prompted, provide the path to your agent's entry point file. This should be the main Python file that runs your agent.

## Example: Optimizing a Customer Support Agent

Let's walk through an example of optimizing a custom customer support agent:

```python
# customer_support_agent.py
import openai

def get_customer_intent(message):
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a customer support agent."},
            {"role": "user", "content": message}
        ]
    )
    return response.choices[0].message.content

def generate_response(intent, message):
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": f"You are a customer support agent. The customer intent is: {intent}"},
            {"role": "user", "content": message}
        ]
    )
    return response.choices[0].message.content

def main():
    customer_message = input("Customer: ")
    intent = get_customer_intent(customer_message)
    response = generate_response(intent, customer_message)
    print(f"Agent: {response}")

if __name__ == "__main__":
    main()
```

After running AIAI CLI optimization on this agent, you might receive recommendations like:

1. "Consider using a cheaper model for intent classification to reduce costs"
2. "Cache intent classifications for similar customer messages"
3. "Add error handling for API calls to improve reliability"

## Interpreting the Results

The optimization report will include:

- **File Paths**: Where in your code the optimizations should be applied
- **Target Functions/Sections**: Which specific functions or code blocks to modify
- **Confidence Scores**: How confident AIAI CLI is in each recommendation
- **Detailed Rules**: Specific recommendations for each optimization

## Applying the Optimizations

To apply the optimizations:

1. Review each recommendation in the report
2. Focus on high-confidence recommendations first
3. Make the suggested changes to your code
4. Re-run your agent to verify improvements
5. Optionally, run AIAI CLI again to identify further optimizations

## Advanced: Custom Evaluation Criteria

For advanced users, AIAI CLI can use custom evaluation criteria to guide optimization:

```bash
# Set environment variables for custom evaluation
export AIAI_EVAL_METRIC="response_time"  # Example: optimize for response time
export AIAI_EVAL_WEIGHT="0.7"  # Weight of this metric (0-1)

# Run AIAI CLI
aiai
```

## Best Practices

When optimizing custom agents with AIAI CLI:

1. **Start Small**: Begin with a simple agent before optimizing complex ones
2. **Focus on Critical Paths**: Prioritize optimizing the most used parts of your agent
3. **Measure Before and After**: Collect metrics before and after optimization to verify improvements
4. **Iterative Approach**: Apply optimizations incrementally and re-run AIAI CLI as needed
5. **Test Thoroughly**: Ensure your agent still functions correctly after optimization 