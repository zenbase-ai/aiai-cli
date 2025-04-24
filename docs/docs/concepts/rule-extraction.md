# Rule Extraction

Rule extraction is one of the core concepts behind AIAI CLI. This page explains what rule extraction is and how it works in the context of agent optimization.

## What is Rule Extraction?

Rule extraction is the process of analyzing execution traces from AI agent runs to identify patterns, bottlenecks, and optimization opportunities. The process converts implicit patterns in execution data into explicit, human-readable rules that can guide optimization efforts.

## How Rule Extraction Works in AIAI CLI

AIAI CLI's rule extraction process follows these steps:

1. **Data Collection**: Execution traces are collected as the agent runs on various inputs.
2. **Pattern Analysis**: The system analyzes the traces to identify recurring patterns, inefficiencies, and bottlenecks.
3. **Rule Formulation**: Patterns are converted into explicit rules with clear recommendations.
4. **Confidence Scoring**: Each rule is assigned a confidence score based on its prevalence and consistency.
5. **Localization**: Rules are mapped to specific locations in the source code.

## Types of Rules

AIAI CLI extracts several types of rules:

### Always Rules

"Always" rules identify patterns that should always be followed. For example:

> "Always cache the results of expensive API calls when the same parameters are used multiple times."

### Never Rules

"Never" rules identify patterns that should be avoided. For example:

> "Never make synchronous API calls in sequence when they could be executed in parallel."

### Tips

"Tips" are general recommendations that may improve performance. For example:

> "Consider using batch processing for multiple, similar database operations to reduce overhead."

## Rule Confidence

Each extracted rule is assigned a confidence score, typically expressed as a percentage. This score reflects how consistently the pattern appears in successful vs. unsuccessful agent runs.

- **High confidence** (80-100%): Strong evidence supports this rule
- **Medium confidence** (50-79%): Moderate evidence supports this rule
- **Low confidence** (0-49%): Limited evidence supports this rule

## Rule Localization

After rules are extracted, AIAI CLI determines where in your code each rule should be applied. This localization process identifies:

- **File paths**: Which files contain the code to be optimized
- **Target sections**: Specific functions or code blocks where the rule applies
- **Context**: Surrounding code that provides context for the optimization

## Viewing Extracted Rules

AIAI CLI generates a markdown report containing all extracted rules, their confidence scores, and their locations in your code. This report is saved to your current directory with a filename like `optimizations_report_20250423_2132.md`.

## Related Concepts

- [Agent Optimization](agent-optimization.md): The overall process of improving agent performance
- [Synthetic Data Generation](../user-guide/configuration.md#synthetic-data-generation): Creating diverse test cases for thorough analysis 