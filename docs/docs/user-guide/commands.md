# Command Reference

AIAI CLI provides several commands to help you optimize your AI agents. This page documents all available commands and their options.

## Basic Usage

```bash
aiai [OPTIONS] [COMMAND]
```

If no command is specified, AIAI CLI runs in interactive mode.

## Global Options

| Option | Description |
|--------|-------------|
| `-V, --version` | Show the version and exit |
| `-q, --quiet` | Silence warnings |
| `-v, --verbose` | Enable verbose output |
| `--color / --no-color` | Force enable or disable color output |
| `--help` | Show help message and exit |

## Interactive Mode

Running `aiai` without a command starts the interactive CLI, which guides you through the optimization process with prompts:

```bash
aiai
```

The interactive mode will:

1. Ask you to choose between optimizing a demo agent or your own agent
2. Validate the agent's entrypoint
3. Analyze the code structure
4. Generate evaluation criteria
5. Run the optimization process
6. Generate a report with recommendations

## Environment Variables

AIAI CLI respects the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for agent evaluation | None |
| `AIAI_EXAMPLES` | Number of synthetic examples to generate | 32 |
| `AIAI_SEED` | Random seed for reproducible synthetic data | 42 |
| `AIAI_CONCURRENCY` | Number of concurrent runs for evaluation | 16 |

You can set these variables in your shell or in a `.env` file in your project directory.

## File Outputs

AIAI CLI generates the following output files:

| File | Description |
|------|-------------|
| `optimizations_report_YYYYMMDD_HHMM.md` | Markdown report with optimization recommendations |
| `db.sqlite3` | SQLite database with execution traces and analysis data |

The database can be useful for advanced analysis and debugging but is not required for normal operation. 