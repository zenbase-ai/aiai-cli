import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

# Assuming your main CLI function is callable, e.g., from aiai.main import cli_app
# If main() is the entrypoint, we might need to adjust how we invoke it.
# For now, let's assume we can import and call the main function directly
# or use a Typer CliRunner if main() is wrapped in a Typer app object.
# Let's refine imports based on the actual structure if needed.
# We'll likely need to import the main function/app object itself.
from aiai.main import cli  # Import the Typer app
from aiai.optimizer.contextualizer import AgentAnalysis, AgentContext, OptimizerPrompts

runner = CliRunner()


@pytest.mark.django_db  # Mark the test as needing DB access for setup
@patch("aiai.main.typer.prompt")
@patch("aiai.main.typer.confirm")
@patch("aiai.main._validate_entrypoint")
@patch("aiai.main.analyze_code")
@patch("aiai.synthesizer.evals.EvalGenerator.perform")  # Mock where it's defined
@patch("aiai.main._optimization_run")
@patch("aiai.main.reset_db")  # Mock reset_db as well
@patch("aiai.main.load_dotenv")  # Don't need .env for this test
@patch.object(sys, "argv", ["aiai"])  # Mock argv for direct function call
def test_cli_demo_agent_success(
    mock_load_dotenv,
    mock_reset_db,
    mock_optimization_run,
    mock_eval_perform,
    mock_analyze_code,
    mock_validate_entrypoint,
    mock_confirm,
    mock_prompt,
    capsys,
):
    """Test the successful path for the demo agent (choice 1)."""
    # --- Arrange Mocks ---
    # Simulate user choosing '1' for demo agent
    mock_prompt.return_value = 1
    # Simulate user confirming 'y' for API key access
    mock_confirm.return_value = True

    # Mock core functions to succeed without doing real work
    mock_validate_entrypoint.return_value = None  # Simulate successful validation
    mock_analyze_code.return_value = AgentContext(
        "",
        AgentAnalysis(
            what="",
            how="",
            success_modes=[],
            failure_modes=[],
            expert_persona="",
            considerations=[],
        ),
        OptimizerPrompts(
            synthetic_data="",
            reward_reasoning="",
            traces_to_patterns="",
            patterns_to_insights="",
            insights_to_rules="",
            synthesize_rules="",
            rule_merger="",
        ),
    )  # Return empty graph
    # Mock EvalGenerator().perform() to return two dummy objects
    mock_eval_perform.return_value = (MagicMock(), MagicMock())
    mock_optimization_run.return_value = None  # Simulate successful run

    # --- Act ---
    # We call the main function directly. If it were a Typer app object,
    # we'd use runner.invoke(app, [...])
    # Use CliRunner to invoke the Typer app
    result = runner.invoke(cli)

    # --- Assert ---
    assert result.exit_code == 0, f"CLI exited with code {result.exit_code}\nOutput:\n{result.output}"

    output = result.output
    print(output)

    assert "🚀 Welcome to aiai! 🤖" in output
    assert "✅ Analyzing code" in output
    assert "✅ Generating evals" in output
    assert "👋 Exiting." in output

    # Verify mocks were called as expected
    mock_prompt.assert_called_once()
    if not os.getenv("OPENAI_API_KEY"):
        mock_confirm.assert_called_once()
    mock_validate_entrypoint.assert_called_once()
    mock_analyze_code.assert_called_once()
    mock_eval_perform.assert_called_once()
    mock_optimization_run.assert_called_once()
    mock_reset_db.assert_called_once()


@pytest.mark.django_db
@patch("aiai.main.typer.prompt")
@patch("aiai.main._validate_entrypoint")
@patch("aiai.main.analyze_code")
@patch("aiai.main._optimization_run")
@patch("aiai.main.reset_db")
@patch("aiai.main.load_dotenv")
@patch.object(sys, "argv", ["aiai", "--custom-eval-file", "test_eval.py"])
def test_cli_with_custom_eval_file(
    mock_load_dotenv,
    mock_reset_db,
    mock_optimization_run,
    mock_analyze_code,
    mock_validate_entrypoint,
    mock_prompt,
    capsys,
):
    """Test the path using a custom evaluation file."""
    # Create a temporary file with a valid custom eval function
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w") as temp_file:
        temp_file.write("""
def main(agent_output):
    return {"reward": 0.75}
        """)
        temp_file.flush()

        custom_eval_path = Path(temp_file.name)

        # Simulate user choosing '2' for custom agent
        mock_prompt.return_value = 2
        # Second prompt is for the entrypoint path
        mock_prompt.side_effect = [2, str(custom_eval_path)]

        # Mock core functions
        mock_validate_entrypoint.return_value = None
        mock_analyze_code.return_value = AgentContext(
            "",
            AgentAnalysis(
                what="",
                how="",
                success_modes=[],
                failure_modes=[],
                expert_persona="",
                considerations=[],
            ),
            OptimizerPrompts(
                synthetic_data="",
                reward_reasoning="",
                traces_to_patterns="",
                patterns_to_insights="",
                insights_to_rules="",
                synthesize_rules="",
                rule_merger="",
            ),
        )

        # Act - invoke CLI with custom eval file
        result = runner.invoke(cli, ["--custom-eval-file", str(custom_eval_path)])

        # Assert
        assert result.exit_code == 0, f"CLI exited with code {result.exit_code}\nOutput:\n{result.output}"
        assert "Using custom evaluation file" in result.output
        assert "Custom evaluation function 'main' loaded successfully" in result.output

        # Verify optimization was run with the custom eval function
        mock_optimization_run.assert_called_once()
        # Get the custom_eval_fn that was passed to _optimization_run
        args, kwargs = mock_optimization_run.call_args
        assert "custom_eval_fn" in kwargs
        assert kwargs["custom_eval_fn"] is not None


@pytest.mark.django_db
@patch("aiai.main.typer.prompt")
@patch("aiai.main._validate_entrypoint")
@patch("aiai.main.analyze_code")
@patch("aiai.main.reset_db")
@patch("aiai.main.load_dotenv")
@patch("aiai.main.generate_data")
def test_custom_eval_function_is_automatically_executed(
    mock_generate_data,
    mock_load_dotenv,
    mock_reset_db,
    mock_analyze_code,
    mock_validate_entrypoint,
    mock_prompt,
    monkeypatch,
):
    """Test that verifies the custom evaluation function is automatically executed during the optimization process."""
    # Create a temporary custom eval file
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w") as temp_file:
        temp_file.write("""
def main(agent_output):
    # This function will be called during the BatchRunner execution
    with open('eval_was_executed.txt', 'w') as f:
        f.write('Custom eval function was executed!')
    return {"reward": 0.75}
        """)
        temp_file.flush()

        # Setup test environment
        custom_eval_path = Path(temp_file.name)
        entrypoint_path = Path(__file__).parent.parent / "examples" / "crewai_agent.py"

        # Generate mock data
        mock_data = ["Test input 1", "Test input 2"]
        mock_generate_data.return_value = [MagicMock(input_data=d) for d in mock_data]

        # Mock user input
        mock_prompt.side_effect = [2, str(entrypoint_path)]

        # Mock validation and analysis
        mock_validate_entrypoint.return_value = None
        mock_analyze_code.return_value = AgentContext(
            "",
            AgentAnalysis(
                what="Test agent", how="", success_modes=[], failure_modes=[], expert_persona="", considerations=[]
            ),
            OptimizerPrompts(
                synthetic_data="",
                reward_reasoning="",
                traces_to_patterns="",
                patterns_to_insights="",
                insights_to_rules="",
                synthesize_rules="",
                rule_merger="",
            ),
        )

        # Patch PyScriptTracer to return mock outputs without running actual scripts
        def mock_tracer_call(self, input_data=None, **kwargs):
            return "mock_trace_id", f"Output for {input_data}"

        # Replace the real BatchRunner.perform with our own implementation
        __import__("aiai.runner.batch_runner").runner.batch_runner.BatchRunner.perform

        def mock_batch_runner_perform(self):
            # Actually call the eval function with test output
            eval_results = []
            for data_item in self.data:
                trace_id = "mock_trace_id"
                output = f"Processed output for: {data_item}"
                # This is the key part: actually calling the evaluation function
                reward = self.eval(output)
                from aiai.app.models import EvalRun

                eval_results.append(EvalRun(trace_id=trace_id, input_data=data_item, output_data=output, reward=reward))
            return eval_results

        # Apply our patches
        with patch("aiai.runner.py_script_tracer.PyScriptTracer.__call__", mock_tracer_call):
            monkeypatch.setattr("aiai.runner.batch_runner.BatchRunner.perform", mock_batch_runner_perform)

            # Clean up any previous test file
            if Path("eval_was_executed.txt").exists():
                Path("eval_was_executed.txt").unlink()

            # Run the CLI with our custom eval file
            runner.invoke(cli, ["--custom-eval-file", str(custom_eval_path)])

            # Verify the evaluation function was called by checking for the file
            assert Path("eval_was_executed.txt").exists()
            content = Path("eval_was_executed.txt").read_text()
            assert content == "Custom eval function was executed!"

            # Clean up
            Path("eval_was_executed.txt").unlink()
