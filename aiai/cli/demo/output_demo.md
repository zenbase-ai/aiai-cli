# Example CLI Output

```
🚀 Welcome to aiai! 🤖

Would you like to optimize:
(1) A built-in demo email agent
(2) Your own agent

> 1

🔑 The demo agent requires an OpenAI API key. Please create a `.env` file in your current directory and add your `OPENAI_API_KEY=sk-...` to it.

Can I access the API key stored in your `.env` file? (y/n)
> y

🔄 Validating entrypoint...
⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏
✅ Entrypoint validated successfully.

📊 Current baseline performance:
- Average response time: 2.3s
- Success rate: 82%

🔄 Resetting analysis database for a fresh run...
⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏
✅ Database reset complete.

🔍 Analyzing your project's code structure and dependencies...
⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏
✅ Code analysis complete.
📈 Found 3 potential optimization areas:
  - Email context handling
  - Response generation
  - Parsing logic

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

🧪 Hypothesis: Integrating all successful optimizations will have compounding benefits
📈 Results:
- Overall performance improvement: +42%
- Response quality: +18%
- Processing speed: +35%

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

1. File: src/agent.py
   - Target: process_email() function
   - Confidence: 92%
   - Rule: Add context caching for repeated email patterns

2. File: src/agent.py
   - Target: generate_response() function
   - Confidence: 88%
   - Rule: Implement response template optimization

3. File: src/prompts/email_classifier.py
   - Target: get_classification_prompt() function
   - Confidence: 94%
   - Rule: Enhance classification prompt with structured format

4. File: src/utils.py
   - Target: parse_email() function
   - Confidence: 85%
   - Rule: Add parallel processing for large email batches

📊 Performance comparison:
| Metric                | Before   | After    | Change |
| --------------------- | -------- | -------- | ------ |
| Response time         | 2.3s     | 1.5s     | -34.8% |
| Email processing rate | 12/min   | 18/min   | +50.0% |
| Response quality      | 72%      | 85%      | +18.1% |
| Overall performance   | Baseline | Enhanced | +42.0% |

✅ Optimization cycle complete.

👋 Exiting.
