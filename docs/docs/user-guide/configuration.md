# Configuration

AIAI CLI can be configured through environment variables and configuration files. This page documents the available configuration options.

## Environment Variables

You can configure AIAI CLI using the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for agent evaluation | None |
| `AIAI_EXAMPLES` | Number of synthetic examples to generate | 32 |
| `AIAI_SEED` | Random seed for reproducible synthetic data | 42 |
| `AIAI_CONCURRENCY` | Number of concurrent runs for evaluation | 16 |

You can set these variables in your shell or in a `.env` file in your project directory.

Example `.env` file:

```bash
OPENAI_API_KEY=sk-your-api-key
AIAI_EXAMPLES=64
AIAI_SEED=123
AIAI_CONCURRENCY=8
```

## Database Configuration

AIAI CLI uses a SQLite database to store execution traces and analysis data. By default, this database is created in the current directory as `db.sqlite3`.

You can customize the database location using the `AIAI_DB_PATH` environment variable:

```bash
AIAI_DB_PATH=/path/to/your/db.sqlite3
```

## Synthetic Data Generation

The synthetic data generation process can be configured with:

- `AIAI_EXAMPLES`: Number of examples to generate (default: 32)
- `AIAI_SEED`: Random seed for reproducible examples (default: 42)

Increasing the number of examples can lead to more thorough analysis but will increase runtime.

## Evaluation Concurrency

AIAI CLI can evaluate your agent on multiple examples concurrently to speed up the optimization process:

- `AIAI_CONCURRENCY`: Number of concurrent evaluations (default: 16)

Adjust this based on your system capabilities. Higher values may improve performance on powerful machines but could cause issues on systems with limited resources.

## OpenAI API Configuration

For the demo agent and some evaluation features, AIAI CLI requires access to the OpenAI API:

- `OPENAI_API_KEY`: Your OpenAI API key
- `OPENAI_MODEL`: OpenAI model to use (default: "gpt-4")
- `OPENAI_MAX_TOKENS`: Maximum tokens per request (default: 2048)

## Advanced Configuration

For advanced users, AIAI CLI supports additional configuration options:

- `AIAI_LOG_LEVEL`: Logging level (default: "INFO")
- `AIAI_DISABLE_TELEMETRY`: Disable anonymous usage telemetry (default: false)
- `AIAI_CACHE_DIR`: Directory for caching results (default: "~/.aiai/cache") 