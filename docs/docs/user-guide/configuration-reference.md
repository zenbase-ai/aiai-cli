# Configuration Reference

This page documents all available configuration options for AIAI CLI. These options can be specified as command-line arguments when running the `aiai` command.

## Command-Line Options

```bash
aiai [OPTIONS]
```

| Option          | Type    | Default             | Description                                              |
| --------------- | ------- | ------------------- | -------------------------------------------------------- |
| `--analyzer`    | TEXT    | openai/o4-mini      | Model used for analyzing code structure and dependencies |
| `--evaluator`   | TEXT    | openai/o4-mini      | Model used for evaluating agent outputs                  |
| `--optimizer`   | TEXT    | openai/gpt-4.1      | Model used for generating optimization rules             |
| `--synthesizer` | TEXT    | openai/gpt-4.1-nano | Model used for generating synthetic data                 |
| `--data`        | PATH    | None                | Path to existing data file                               |
| `--examples`    | INTEGER | 25                  | Number of synthetic examples to generate                 |
| `--seed`        | INTEGER | 42                  | Random seed for reproducible synthetic data              |
| `--concurrency` | INTEGER | 16                  | Number of concurrent evaluations                         |

## Understanding Configuration Options

### Model Selection Options

AIAI CLI uses different models for specific tasks in the optimization pipeline. You can customize which models are used for each task. AIAI CLI supports all models available through [LiteLLM](https://docs.litellm.ai/docs/providers), allowing you to use models from various providers like OpenAI, Anthropic, Google, and many others.

Models are specified using LiteLLM's format: `provider/model-name`.

#### --analyzer

The analyzer model is responsible for examining your agent's code structure and building a dependency graph.

```bash
aiai --analyzer="openai/gpt-4o-mini"
```

#### --evaluator

The evaluator model assesses agent outputs against generated criteria. This model determines how well your agent performs on synthetic examples.

```bash
aiai --evaluator="azure/<your_deployment_name>"
```

#### --optimizer

The optimizer model is responsible for generating optimization rules based on execution patterns. This is the most critical model in the pipeline, as it directly impacts the quality of recommendations.

```bash
aiai --optimizer="anthropic/claude-3-opus"
```

#### --synthesizer

The synthesizer model generates diverse examples to test your agent. This model needs to create varied, realistic test cases.

```bash
aiai --synthesizer="google/gemini-pro"
```

### Model Provider Setup

Since AIAI CLI uses LiteLLM under the hood, you need to set up API keys and other configuration for model providers exactly the same way you would with LiteLLM. This is done through environment variables.

#### Environment Variables

Set the appropriate environment variables for your chosen model providers before running AIAI CLI:

```bash
# OpenAI
export OPENAI_API_KEY=your_openai_api_key

# Azure OpenAI
export AZURE_API_KEY=your_azure_api_key
export AZURE_API_BASE=your_azure_endpoint  # e.g., https://your-resource.openai.azure.com/
export AZURE_API_VERSION=your_api_version  # e.g., 2023-05-15

# Other providers
# See LiteLLM documentation for full list of supported providers and required environment variables
```

For a complete list of supported providers and their required environment variables, refer to the [LiteLLM documentation](https://docs.litellm.ai/docs/providers).

#### --data

Path to existing data file. If not provided, AIAI CLI will generate synthetic data.

```bash
aiai --data="data.json"
```

data.json should be a JSON file with a list of inputs.

```json
[
    "input1",
    "input2",
]
```

### Synthetic Data Options

Controls how many synthetic examples are generated to test your agent. More examples provide better coverage but increase runtime.

```bash
aiai --examples=20
```

!!! note "Maximum Examples"
    The maximum number of synthetic examples is capped at 25 by default. If you specify a larger number, it will be reduced to 25.

#### --seed

Sets the random seed for synthetic data generation. Using the same seed ensures reproducible results across different runs.

```bash
aiai --seed=12345
```

### Performance Options

#### --concurrency

Controls how many agent evaluations run in parallel. Higher concurrency speeds up the process but increases resource usage.

```bash
aiai --concurrency=8
```

## Example Usage

### Basic Usage

```bash
aiai
```

### Custom Configuration

```bash
aiai --optimizer="openai/gpt-4o" --examples=20 --concurrency=8
```

### Comprehensive Custom Configuration

```bash
aiai \
--analyzer="openai/o4-mini" \
--evaluator="openai/o4-mini" \
--optimizer="anthropic/claude-3-opus" \
--synthesizer="google/gemini-pro" \
--examples=25 \
--seed=12345 \
--concurrency=8
```

### Using Different Model Providers

Here's an example that uses Azure OpenAI models:

```bash
# First set required environment variables for Azure OpenAI
export AZURE_API_KEY=your_azure_api_key
export AZURE_API_BASE=https://your-resource.openai.azure.com/
export AZURE_API_VERSION=2023-05-15

# Then run AIAI with Azure OpenAI models
# Format for Azure: azure/<your-deployment-name>
aiai \
--analyzer="azure/gpt-4o-mini" \
--evaluator="azure/gpt-4o" \
--optimizer="azure/gpt-4-turbo" \
--synthesizer="azure/gpt-4o"
```

## Custom Evaluation

Instead of using AIAI's automatically generated evaluation criteria, you can provide your own custom evaluation function in your entrypoint file:


1. Define a function named `eval` in your entrypoint file that takes a single parameter (agent_output)
2. The function can return any output format needed for your evaluation


```python
def eval(agent_output):
    """Custom evaluation function"""
    # Your evaluation logic here
    # Example 1: Return a dictionary with multiple metrics
    return {
        "conciseness": 0.85,
        "relevance": 0.92,
        "accuracy": 0.78,
        "overall_score": 0.85
    }
    
    # Example 2: Return a simple score
    # return 0.85
    
    # Example 3: Return a boolean
    # return agent_output.startswith("The answer is")
```

When detected, this function will be used instead of the default evaluator. For a complete example, see [Adding Custom Evaluation Functions](../examples/custom-agents.md#adding-custom-evaluation-functions).

## Related Topics

- [Installation](../getting-started/getting-started.md)
- [Custom Agents](../examples/custom-agents.md)
- [LiteLLM Documentation](https://docs.litellm.ai/docs/)
