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
from aiai.cli.app import app as cli_app  # Import the Typer app
from aiai.code_analyzer.graph import DependencyGraph

runner = CliRunner()


@pytest.fixture(autouse=True)
def setup_test_db():
    """Ensure Django is set up for each test using the test database."""
    # setup_django() # Now called automatically via aiai/__init__.py import
    pass


@pytest.mark.django_db  # Mark the test as needing DB access for setup
@patch("aiai.cli.app.typer.prompt")
@patch("aiai.cli.app.typer.confirm")
@patch("aiai.cli.app._validate_entrypoint")
@patch("aiai.cli.app.analyze_code")
@patch("aiai.synthesizer.evals.EvalGenerator.perform")  # Mock where it's defined
@patch("aiai.cli.app._optimization_run")
@patch("aiai.cli.app.reset_db")  # Mock reset_db as well
@patch("aiai.cli.app.load_dotenv")  # Don't need .env for this test
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
    result = runner.invoke(cli_app)

    # --- Assert ---
    assert result.exit_code == 0, f"CLI exited with code {result.exit_code}\nOutput:\n{result.output}"

    output = result.output

    # Check for key messages indicating the flow proceeded correctly
    assert "🚀 Welcome to aiai! 🤖" in output
    assert "🔑 The demo agent requires an OpenAI API key" in output
    # We mocked validation, so we don't see the spinner message, but the success one
    assert "✅ Entrypoint validated successfully." in output
    assert "🔄 Resetting analysis database" in output  # reset_db is called
    assert "✅ Database reset complete." in output
    assert "🔍 Analyzing your project's code structure" in output
    assert "✅ Code analysis complete." in output
    assert "📝 Generating evaluation criteria" in output
    # Because loading() replaces the line, the simple success message isn't there.
    # We rely on the exit code and mock calls for success verification.
    # assert "✅ Evaluation criteria generated." in output
    assert "🔄 Starting the optimization run…" in output
    # _optimization_run is mocked, so its internal messages won't appear
    assert "👋 Exiting." in output

    # Verify mocks were called as expected
    mock_prompt.assert_called_once()
    mock_confirm.assert_called_once()
    mock_validate_entrypoint.assert_called_once()
    mock_analyze_code.assert_called_once()
    mock_eval_perform.assert_called_once()
    mock_optimization_run.assert_called_once()
    mock_reset_db.assert_called_once()
