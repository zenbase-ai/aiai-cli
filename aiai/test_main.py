import sys
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

# Assuming your main CLI function is callable, e.g., from aiai.main import cli_app
# If main() is the entrypoint, we might need to adjust how we invoke it.
# For now, let's assume we can import and call the main function directly
# or use a Typer CliRunner if main() is wrapped in a Typer app object.
# Let's refine imports based on the actual structure if needed.
# We'll likely need to import the main function/app object itself.
from aiai.__main__ import cli  # Import the Typer app
from aiai.code_analyzer.graph import DependencyGraph

runner = CliRunner()


@pytest.mark.django_db  # Mark the test as needing DB access for setup
@patch("aiai.__main__.typer.prompt")
@patch("aiai.__main__.typer.confirm")
@patch("aiai.__main__._validate_entrypoint")
@patch("aiai.__main__.analyze_code")
@patch("aiai.synthesizer.evals.EvalGenerator.perform")  # Mock where it's defined
@patch("aiai.__main__._optimization_run")
@patch("aiai.__main__.reset_db")  # Mock reset_db as well
@patch("aiai.__main__.load_dotenv")  # Don't need .env for this test
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
    mock_analyze_code.return_value = DependencyGraph()  # Return empty graph
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
    assert "🔑 The demo agent requires an OpenAI API key" in output
    assert "✅ Analyzing code" in output
    assert "✅ Generating evals" in output
    assert "👋 Exiting." in output

    # Verify mocks were called as expected
    mock_prompt.assert_called_once()
    mock_confirm.assert_called_once()
    mock_validate_entrypoint.assert_called_once()
    mock_analyze_code.assert_called_once()
    mock_eval_perform.assert_called_once()
    mock_optimization_run.assert_called_once()
    mock_reset_db.assert_called_once()
