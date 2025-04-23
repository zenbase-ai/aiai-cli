**`aiai` CLI: AI Agent Optimization Workflow** 🚀

**Goal:** To provide a simple, command-line driven experience for analyzing and optimizing AI agents, starting with `crewai` agents. The CLI automates code analysis, data generation, evaluation, and rule discovery.

**User Invocation:**

1.  The user installs the tool: `pip install aiai`
2.  The user runs the command: `aiai`

**Initialization & Setup:**

3.  The CLI starts and asks the user: "Welcome to `aiai`! 🤖 Would you like to optimize:\n (1) A built-in demo email agent\n (2) Your own agent "
4. Show an example entrypoint for running it with your own agent
    *   The CLI displays an example entrypoint.py file:
        ```python
        # Example entrypoint.py
        from your_app import YourAgent

        def main(input_data = None):
            example = input_data or "..."
            agent = YourAgent()
            result = agent.kickoff({"input": example})
            return result
        ```
5.  **If Demo (1):**
    *   The CLI informs the user: "The demo agent requires an OpenAI API key. 🔑 Please create a `.env` file in your current directory and add your `OPENAI_API_KEY=sk-...` to it."
    *   The CLI then asks for permission: "Can I access the API key stored in your `.env` file? (y/n)"
    *   If 'y', it prepares to use a pre-configured `entrypoint.py` from the crewai example in `aiai/examples/crewai/entrypoint.py`.
    *   If 'n', it explains API keys are needed and exits.
6.  **If User Agent (2):**
    *   The CLI prompts: "Please provide the path to your agent's entrypoint file (e.g., `src/my_agent_main.py`). 📂 This file must have a `main()` function that runs your agent."
    *   The user provides the path.

**Validation:**

6.  The CLI attempts to run the specified `entrypoint.py` using `PyScriptTracer` to ensure it's executable and capture its execution.
```python
with PyScriptTracer(self.script) as tracer:
    trace_id, output_data = tracer()
```

7.  **If Failure:**
    *   Demo: "❌ Failed to run the demo agent. Error details:\n```\n<traceback details>\n```"
    *   User Agent: "❌ Failed to execute your entrypoint file at `<path>`. Please ensure it runs correctly and includes your agent logic. Exiting."
8.  **If Success:** "✅ Entrypoint validated successfully."

**Analysis & Preparation:**

9.  "🔄 Resetting analysis database for a fresh run..." (The CLI clears any previous run data).
10. "🔍 Analyzing your project's code structure and dependencies..." (Runs `CodeAnalyzer.analyze_project()` to store `FunctionInfo`, etc.).
11. "📊 Analyzing project data files (JSON/YAML) for LLM relevance..." (Runs `DataFileAnalyzer.analyze()` to store `DataFileAnalysis`).
12. "📝 Generating evaluation criteria based on the analysis..." (Runs `EvalGenerator.perform()` to create `SyntheticEval` entries in the database for 'rules' and 'head_to_head' evaluations).

**Iterative Optimization Cycle:**

13. "🔄 Starting the optimization cycle..." The CLI enters a loop (e.g., 5 epochs by default). Let `N` be the current epoch number (starting at 1).
14. **Evaluation Run (Epoch `N`):**
    *   "📊 Running evaluation for Epoch `N`..."
    *   If `N == 1`: Runs the agent against a subset of synthetic data using `SyntheticEvalRunner` with the `SyntheticEval` of `kind='rules'`.
    *   If `N > 1`: Runs the agent against a subset of synthetic data using `SyntheticEvalRunner` with the `SyntheticEval` of `kind='head_to_head'`.
    *   The execution trace is logged (e.g., using `OtelSpan`) and tagged with `epoch=N`. # TODO: Confirm epoch tagging implementation
    *   Each evaluation run is logged to the database using EvalRun
15. **Rule Discovery (Epoch `N`):**
    *   "🔍 Analyzing run results to discover optimization rules for Epoch `N`..." (Runs `rule_extractor.extract_rules` on the `OtelSpan` data for the current epoch).
16. **Rule Merging:**
    *   "🔄 Merging newly discovered rules..." (The rules from Epoch `N` are combined with the set of rules from previous epochs using `rule_merger.merge_rules`). Let this merged set be `current_rules`.
17. **Loop Check:**
    *   If `N` is less than the total number of epochs: Increment `N` and go back to step 14.
    *   If `N` equals the total number of epochs: Proceed to Completion with `current_rules`.

**Completion:**

18. **Rule Locator:**
    *   "📍 Locating where to apply the final rules..." (Runs `RuleLocator(current_rules).perform()` which identifies target code sections and saves them as `DiscoveredRule` entries in the database).
19. "✅ Optimization cycle complete."
20. "📋 Final discovered optimization rule placements:"
    *   The CLI displays the final set of `DiscoveredRule` objects (including file paths, target code sections, and confidence scores) found during the process.
21. "👋 Exiting."
