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

AIAI CLI uses different models for specific tasks in the optimization pipeline. You can customize which models are used for each task:

#### --analyzer

The analyzer model is responsible for examining your agent's code structure and building a dependency graph.

```bash
aiai --analyzer="openai/gpt-4o-mini"
```

#### --evaluator

The evaluator model assesses agent outputs against generated criteria. This model determines how well your agent performs on synthetic examples.

```bash
aiai --evaluator="openai/gpt-4o"
```

#### --optimizer

The optimizer model is responsible for generating optimization rules based on execution patterns. This is the most critical model in the pipeline, as it directly impacts the quality of recommendations.

```bash
aiai --optimizer="openai/gpt-4.1"
```

#### --synthesizer

The synthesizer model generates diverse examples to test your agent. This model needs to create varied, realistic test cases.

```bash
aiai --synthesizer="openai/gpt-4o"
```

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
--synthesizer="openai/gpt-4o" \
--examples=25 \
--seed=12345 \
--concurrency=8
```

## Related Topics

- [Installation](../getting-started/getting-started.md)
- [Custom Agents](../examples/custom-agents.md)
