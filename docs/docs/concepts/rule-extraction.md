# Rule Extraction

Rule extraction is one of the core concepts behind AIAI CLI. This page explains what rule extraction is and how it works in the context of agent optimization.

## What is Rule Extraction?

Rule extraction is the process of analyzing execution traces from AI agent runs to identify patterns, bottlenecks, and optimization opportunities. The process converts implicit patterns in execution data into explicit, human-readable rules that can guide optimization efforts.

## How Rule Extraction Works in AIAI CLI

AIAI CLI's rule extraction process follows these steps:

1. **Data Collection**: Execution traces are collected as the agent runs on various inputs.
2. **Pattern Analysis**: The system analyzes the traces to identify recurring patterns, inefficiencies, and bottlenecks.
3. **Rule Formulation**: Patterns are converted into explicit rules with clear recommendations.
4. **Localization**: Rules are mapped to specific locations in the source code.

## Types of Rules

AIAI CLI extracts several types of rules:

### Always Rules

"Always" rules identify patterns that should always be followed. For example:

> "Always break down complex reasoning tasks into step-by-step explanations before providing the final answer."

### Never Rules

"Never" rules identify patterns that should be avoided. For example:

> "Never provide vague or general responses that lack specific details or context-relevant information."

### Tips

"Tips" are general recommendations that may improve performance. For example:

> "Consider illustrating your reasoning with concrete examples when explaining complex concepts."

## Rule Localization

After rules are extracted, AIAI CLI determines where in your code each rule should be applied. This localization process identifies:

- **File paths**: Which files contain the code to be optimized
- **Target sections**: Specific functions or code blocks where the rule applies
- **Context**: Surrounding code that provides context for the optimization

## Viewing Extracted Rules

AIAI CLI generates a markdown report containing all extracted rules, and their locations in your code. This report is saved to your current directory with a filename like `optimizations_report_20250423_2132.md`.

## Agent Optimization Process

AIAI CLI follows a systematic process to optimize AI agents:

1. **Code Analysis**: The system analyzes your agent's source code to understand its structure, dependencies, and components, building a dependency graph.
2. **Synthetic Data Generation**: AIAI CLI generates diverse synthetic test cases that will be used to exercise your agent's functionality and collect execution data.
3. **Evaluation Criteria Generation**: The system creates evaluation criteria based on the code analysis, which will be used to assess your agent's performance.
4. **Execution Tracing**: Your agent is run against the synthetic data to collect detailed execution traces, capturing information about API calls, function execution, and performance metrics.
5. **Rule Extraction**: Patterns identified in the execution traces are converted into explicit optimization rules.
6. **Rule Localization**: Rules are mapped to specific locations in your agent's source code where they should be applied.
7. **Report Generation**: Finally, AIAI CLI produces a comprehensive optimization report with actionable recommendations, file paths, target code sections.
