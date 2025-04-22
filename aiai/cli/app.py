import io
import textwrap
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from datetime import datetime
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.progress import Progress, SpinnerColumn, TextColumn

from aiai.code_analyzer import CodeAnalyzer
from aiai.optimizer.rule_extractor import extract_rules
from aiai.optimizer.rule_locator import RuleLocator
from aiai.optimizer.rule_merger import Rules
from aiai.runner.py_script_tracer import PyScriptTracer
from aiai.runner.runner import Runner
from aiai.runner.runner import Runner as BatchRunner
from aiai.synthesizer.data import DataGenerator
from aiai.synthesizer.evals import EvalGenerator, SyntheticEvalRunner

# Use absolute imports within the package
from aiai.utils import reset_db

# ---------------------------------------------------------------------------
# Utility: silence stdout/stderr and loading spinner
# ---------------------------------------------------------------------------


@contextmanager
def silence():
    """Temporarily suppress *all* stdout / stderr output (prints, progress bars, etc.)."""
    new_out, new_err = io.StringIO(), io.StringIO()
    with redirect_stdout(new_out), redirect_stderr(new_err):
        yield


@contextmanager
def loading(message: str):
    """Show pretty Rich spinner while silencing inner output."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description=message, total=None)
        with silence():
            yield


def analyze_code(file: Path):
    # No need for inner import now
    analyzer = CodeAnalyzer()
    graph = analyzer.analyze_from_file(file, save_to_db=True)
    return graph


def capture_logs(file: Path):
    # No need for inner import now
    Runner().run_script(file)


# --- New helper --------------------------------------------------------------


def _validate_entrypoint(entrypoint: Path) -> None:
    """Run the entrypoint once to make sure it is executable.

    This reuses `ScriptTracer` so the run is fully traced and stored
    in OpenTelemetry. Any exception bubbles up to the caller so the CLI
    can present a helpful error message.
    """
    # Ensure Django is configured so that ScriptTracer import succeeds.
    # setup_django() # Now called in aiai/__init__.py

    # No need for inner import now
    with loading("Validating entrypoint…"):
        with PyScriptTracer(entrypoint) as tracer:
            tracer()


# --- Optimization loop -------------------------------------------------------


def _optimization_run(
    entrypoint: Path,
    rules_eval,
    *,
    examples: int = 32,
    seed: int = 42,
    concurrency: int = 16,
):
    """Run a single optimisation pass (no epochs)."""
    # Import models here, after setup_django has run
    from aiai.app.models import OtelSpan, SyntheticDatum

    # ------------------------------------------------------------------
    # Generate synthetic data (or reuse if already present)
    # ------------------------------------------------------------------
    if SyntheticDatum.objects.count() == 0:
        typer.echo("Generating synthetic data examples…")
        with loading("Generating synthetic data examples…"):
            DataGenerator(examples=examples, seed=seed).perform()
        typer.secho("", nl=False)  # spacer

    data_inputs = [d.input_data for d in SyntheticDatum.objects.all()[:examples]]

    current_rules: Rules | dict = {"always": [], "never": [], "tips": []}

    eval_runner = SyntheticEvalRunner(rules_eval)

    def _score_fn(output: str):
        return eval_runner(output).get("reward", 0)

    typer.echo("📊 Running evaluation…")
    batch_runner = BatchRunner(
        script=entrypoint,
        data=data_inputs,
        eval=_score_fn,
        concurrency=concurrency,
    )
    with loading("Running evaluation…"):
        batch_runner.perform()
    typer.secho("", nl=False)

    typer.echo("🔍 Analyzing run results to discover optimization rules…")
    logs = OtelSpan.objects.all()
    with loading("Extracting optimization rules…"):
        current_rules = extract_rules(logs)
    typer.secho("", nl=False)

    # ------------------------------------------------------------------
    # Rule placement
    # ------------------------------------------------------------------
    typer.echo("📍 Locating where to apply the final rules…")
    with loading("Locating rule placements…"):
        placements = RuleLocator(current_rules).perform()
    typer.secho("", nl=False)

    # ------------------------------------------------------------------
    # Display placements & save to markdown
    # ------------------------------------------------------------------
    if placements:
        typer.echo("\n📋 Final discovered optimization rule placements:\n")

        # Pretty console output (similar to earlier demos)
        for idx, p in enumerate(placements, start=1):
            target = p.get("target_code_section") or p.get("function_name", "")
            target = textwrap.shorten(str(target).replace("\n", " "), width=80, placeholder="…")
            rule_text = textwrap.shorten(p.get("rule_text", "").strip(), width=100, placeholder="…")
            typer.echo(
                f"{idx}. File: {p.get('file_path', 'N/A')}\n"
                f"   - Target: {target}\n"
                f"   - Confidence: {p.get('confidence', 'N/A')}%\n"
                f"   - Rule: {rule_text}\n"
            )

        # Markdown table
        md_lines = [
            "# Final discovered optimization rule placements\n",
            "| # | File | Target | Confidence | Rule |",
            "| --- | --- | --- | --- | --- |",
        ]
        for idx, p in enumerate(placements, start=1):
            file_path = p.get("file_path", "N/A")
            target = (p.get("target_code_section") or p.get("function_name", "")).replace("\n", " ")
            conf = p.get("confidence", "N/A")
            rule = p.get("rule_text", "").replace("|", "\|")
            md_lines.append(
                f"| {idx} | {file_path} | {textwrap.shorten(target, width=40, placeholder='…')} | {conf} "
                f"| {textwrap.shorten(rule, width=60, placeholder='…')} |"
            )

        md_content = "\n".join(md_lines)
        report_path = Path(f"optimizations_report_{datetime.now():%Y%m%d_%H%M}.md")
        report_path.write_text(md_content)
        typer.echo(f"\n📝 Generated optimization report saved to: {report_path}\n")
    else:
        typer.echo("⚠️  No rule placements found.")


# Renamed main function to avoid clash
def run_cli() -> None:  # noqa: C901 – the CLI can be a bit long
    """Interactive `aiai` CLI as described in `aiai/cli/README.md`."""

    # Early imports kept local to speed up `python -m aiai` startup.
    load_dotenv()

    # Defaults for synthetic data generation
    examples = 32
    seed = 42

    typer.secho("\n🚀 Welcome to aiai! 🤖\n", fg=typer.colors.BRIGHT_CYAN, bold=True)

    # ------------------------------------------------------------------
    # 1️⃣  Agent selection
    # ------------------------------------------------------------------
    choice_prompt = "Would you like to optimize:\n (1) A built‑in demo email agent\n (2) Your own agent"
    choice = typer.prompt(choice_prompt, type=int)

    if choice == 1:
        typer.echo(
            "\n🔑 The demo agent requires an OpenAI API key. Please create a `.env` file in your "
            "current directory and add your `OPENAI_API_KEY=sk-...` to it.\n"
        )
        if not typer.confirm("Can I access the API key stored in your `.env` file?", default=False):
            raise typer.Exit(code=1)

        # Path to the pre‑configured demo entrypoint
        # NOTE: This path needs adjustment when run from cli/app.py
        # Let's assume the script is run from the project root for now,
        # or we pass the root path explicitly.
        # For simplicity, using a relative path from expected root execution
        entrypoint = Path("aiai/examples/crewai/entrypoint.py").resolve()

    elif choice == 2:
        entrypoint_str = typer.prompt(
            "\n📂 Please provide the path to your agent's entrypoint file (e.g., "
            "`src/my_agent_main.py`). This file must have a `main()` function that runs "
            "your agent."
        )
        entrypoint = Path(entrypoint_str).expanduser().resolve()
        if not entrypoint.exists():
            typer.secho(f"❌ Entrypoint file not found: {entrypoint}", fg=typer.colors.RED)
            raise typer.Exit(code=1)
    else:
        typer.secho("❌ Invalid choice. Exiting.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # ------------------------------------------------------------------
    # 2️⃣  Entrypoint validation
    # ------------------------------------------------------------------
    typer.echo("\n🔄 Validating entrypoint…")
    try:
        _validate_entrypoint(entrypoint)
    except Exception as exc:  # noqa: BLE001 – show raw error to user
        typer.secho(f"❌ Failed to run the entrypoint. Error details:\n{exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    typer.secho("✅ Entrypoint validated successfully.\n", fg=typer.colors.GREEN)

    # ------------------------------------------------------------------
    # 3️⃣  Analysis setup
    # ------------------------------------------------------------------
    typer.echo("🔄 Resetting analysis database for a fresh run…")
    # setup_django() # Now called in aiai/__init__.py
    reset_db()
    typer.secho("✅ Database reset complete.\n", fg=typer.colors.GREEN)

    # ------------------------------------------------------------------
    # 4️⃣  Code analysis ➜ Dependency graph
    # ------------------------------------------------------------------
    typer.echo("🔍 Analyzing your project's code structure and dependencies…")
    graph = analyze_code(entrypoint)
    typer.secho("✅ Code analysis complete.", fg=typer.colors.GREEN)
    typer.echo(f"📈 Found {len(graph.functions)} functions.\n")

    # ------------------------------------------------------------------
    # 5️⃣  Evaluation criteria generation
    # ------------------------------------------------------------------
    typer.echo("📝 Generating evaluation criteria based on the analysis…")
    try:
        # No need for inner import now
        from aiai.app.models import FunctionInfo

        generator = EvalGenerator()
        rules_eval, _ = generator.perform(list(FunctionInfo.objects.all()))  # Ignore head_to_head
        typer.secho("✅ Evaluation criteria generated.\n", fg=typer.colors.GREEN)
    except Exception as exc:  # noqa: BLE001 – non‑critical failure
        typer.secho(
            f"⚠️  Skipped evaluation criteria generation due to error: {exc}\n",
            fg=typer.colors.YELLOW,
        )
        rules_eval = None

    # ------------------------------------------------------------------
    # 6️⃣  Optimization run
    # ------------------------------------------------------------------
    if rules_eval:
        typer.echo("🔄 Starting the optimization run…")
        _optimization_run(
            entrypoint,
            rules_eval,
            examples=examples,
            seed=seed,
        )
    else:
        typer.secho(
            "⚠️  Optimisation run skipped because evaluation criteria were not generated.\n",
            fg=typer.colors.YELLOW,
        )

    typer.secho("👋 Exiting.\n", fg=typer.colors.BRIGHT_CYAN, bold=True)


# --- Typer hook --------------------------------------------------------------

# Define the Typer app instance
app = typer.Typer()

# Register the command
app.command()(run_cli)

if __name__ == "__main__":
    # This allows running `python -m aiai.cli.app` directly
    # Set up Django FIRST when running as main script
    # setup_django() # Now called in aiai/__init__.py
    app()
