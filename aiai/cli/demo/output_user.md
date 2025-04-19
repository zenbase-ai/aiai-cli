# Example CLI Output (Custom Agent)

```
🚀 Welcome to aiai! 🤖

Would you like to optimize:
(1) A built-in demo email agent
(2) Your own agent

> 2

📂 Please provide the path to your agent's entrypoint file (e.g., `src/my_agent_main.py`). This file must have a `main()` function that runs your agent.

> src/agents/customer_service.py

🔄 Validating entrypoint...
⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏
✅ Entrypoint validated successfully.

🔍 Detected agent type: Customer Service Agent
📊 Found 3 main components:
- Customer intent classification
- Response generation
- Ticket routing

📊 Current baseline performance:
- Average response time: 3.2s
- Intent classification accuracy: 78%
- Customer satisfaction score: 72%
- Memory usage: 520MB
- Ticket routing accuracy: 83%

🔄 Resetting analysis database for a fresh run...
⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏
✅ Database reset complete.

🔍 Analyzing your project's code structure and dependencies...
⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏
✅ Code analysis complete.
📈 Found 5 potential optimization areas:
  - Intent classification algorithm
  - Response generation templates
  - Ticket routing logic
  - Context management
  - Response validation

📊 Analyzing project data files (JSON/YAML) for LLM relevance...
⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏
✅ Data file analysis complete.

📝 Generating evaluation criteria based on the analysis...
⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏
✅ Evaluation criteria generated.

🔄 Starting the optimization cycle...

Epoch 1/5
📊 Running evaluation...
⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏
✅ Evaluation complete.

🔍 Analyzing run results to discover optimization rules...
⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏
✅ Rules discovered.

🔄 Merging newly discovered rules...
⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏
✅ Rules merged.

Epoch 2/5
📊 Running evaluation...
⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏
✅ Evaluation complete.

🔍 Analyzing run results to discover optimization rules...
⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏
✅ Rules discovered.

🔄 Merging newly discovered rules...
⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏
✅ Rules merged.

Epoch 3/5
📊 Running evaluation...
⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏
✅ Evaluation complete.

🔍 Analyzing run results to discover optimization rules...
⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏
✅ Rules discovered.

🔄 Merging newly discovered rules...
⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏
✅ Rules merged.

Epoch 4/5
📊 Running evaluation...
⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏
✅ Evaluation complete.

🔍 Analyzing run results to discover optimization rules...
⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏
✅ Rules discovered.

🔄 Merging newly discovered rules...
⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏
✅ Rules merged.

Epoch 5/5
📊 Running evaluation...
⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏
✅ Evaluation complete.

🔍 Analyzing run results to discover optimization rules...
⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏
✅ Rules discovered.

🔄 Merging newly discovered rules...
⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏
✅ Rules merged.

📍 Locating where to apply the final rules...
⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏
✅ Rule locations identified.

📋 Final discovered optimization rule placements:

1. File: src/agents/customer_service.py
   - Target: classify_intent() function
   - Confidence: 95%
   - Rule: Implement intent caching for common customer queries

2. File: src/agents/prompts/intent_classifier.py
   - Target: get_intent_prompt() function
   - Confidence: 93%
   - Rule: Enhance intent classification prompt with structured format

3. File: src/agents/prompts/response_generator.py
   - Target: build_response_prompt() function
   - Confidence: 92%
   - Rule: Add comprehensive context and guidelines to response prompts

4. File: src/agents/ticket_router.py
   - Target: route_ticket() function
   - Confidence: 88%
   - Rule: Implement priority-based routing optimization

5. File: src/agents/context_manager.py
   - Target: update_context() function
   - Confidence: 85%
   - Rule: Add smart context pruning for long conversations

📊 Performance comparison:
| Metric                    | Before   | After    | Change |
| ------------------------- | -------- | -------- | ------ |
| Total response time       | 3.2s     | 1.5s     | -53.1% |
| Intent classification     | 78%      | 91%      | +16.7% |
| Customer satisfaction     | 72%      | 86%      | +19.4% |
| Memory usage (avg)        | 520MB    | 480MB    | -7.7%  |
| Memory usage (long conv.) | 820MB    | 530MB    | -35.4% |
| Ticket routing accuracy   | 83%      | 85%      | +2.4%  |
| Urgent ticket response    | 15min    | 5min     | -66.7% |
| Overall performance       | Baseline | Enhanced | +42.0% |

📊 Performance Summary:
- Total potential speedup: 2.1x
- Memory usage reduction: 35%
- Expected accuracy improvement: 16.7%
- Customer satisfaction improvement: 19.4%

✅ Optimization cycle complete.

💡 Would you like to:
(1) Apply all optimizations
(2) Review and select specific optimizations
(3) Save recommendations for later

> 1

🔄 Applying optimizations...
⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏
✅ Optimizations applied successfully.

📝 Generated optimization report saved to: optimizations_report_20240321_1530.md

👋 Exiting.
