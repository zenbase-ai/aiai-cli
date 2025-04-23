import io
import json
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from time import monotonic

import rich
import typer
from dotenv import load_dotenv
from rich.progress import Progress, SpinnerColumn, TextColumn

from aiai.app.models import FunctionInfo
from aiai.code_analyzer import CodeAnalyzer
from aiai.optimizer.contextualizer import AgentContext, generate_context
from aiai.optimizer.rule_extractor import generate_rules_and_tips
from aiai.optimizer.rule_locator import RuleLocator
from aiai.runner.batch_runner import BatchRunner
from aiai.runner.py_script_tracer import PyScriptTracer
from aiai.synthesizer.data import generate_data
from aiai.synthesizer.evals import EvalGenerator, RulesEval, SyntheticEvalRunner

# Use absolute imports within the package
from aiai.utils import reset_db

# ---------------------------------------------------------------------------
# Utility: silence stdout/stderr and loading spinner
# ---------------------------------------------------------------------------


@contextmanager
def silence():
    """Temporarily suppress *all* stdout / stderr output (prints, progress bars, etc.)."""
    stdout, stderr = io.StringIO(), io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        yield stdout, stderr


@contextmanager
def loading(message: str):
    """Show pretty Rich spinner while silencing inner output."""
    start_at = monotonic()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description=message, total=None)
        with silence():
            yield
    duration = monotonic() - start_at
    typer.secho(f"✅ {message} completed in {duration:.2f}s", fg=typer.colors.GREEN)


def analyze_code(file: Path, model: str) -> AgentContext:
    # No need for inner import now
    analyzer = CodeAnalyzer()
    analyzer.analyze_from_file(file, save_to_db=True)
    source_code = json.dumps(
        {name: source_code for name, source_code in FunctionInfo.objects.values_list("name", "source_code")},
    )
    context = generate_context(source_code=source_code, model=model)
    rich.print_json(context.analysis.model_dump_json())
    return context


# --- New helper --------------------------------------------------------------


def _validate_entrypoint(entrypoint: Path) -> None:
    """Run the entrypoint once to make sure it is executable.

    This reuses `ScriptTracer` so the run is fully traced and stored
    in OpenTelemetry. Any exception bubbles up to the caller so the CLI
    can present a helpful error message.
    """
    # No need for inner import now
    with loading("Validating entrypoint…"):
        with PyScriptTracer(entrypoint) as tracer:
            tracer()


# --- Optimization loop -------------------------------------------------------


def _optimization_run(
    entrypoint: Path,
    rules_eval: RulesEval,
    context: AgentContext,
    model: str,
    examples: int,
    concurrency: int,
    seed: int,
):
    """Run a single optimisation pass (no epochs)."""
    # Import models here, after setup_django has run
    from aiai.app.models import SyntheticDatum

    # ------------------------------------------------------------------
    # Generate synthetic data (or reuse if already present)
    # ------------------------------------------------------------------
    data = SyntheticDatum.objects.all()
    if len(data) == 0:
        with loading(f"Generating {examples} synthetic data examples…"):
            data = generate_data(context, examples, seed, model)

    eval_runner = SyntheticEvalRunner(rules_eval, model=model)
    batch_runner = BatchRunner(
        script=entrypoint,
        data=[d.input_data for d in data],
        eval=lambda output: eval_runner(output).get("reward", 0),
        concurrency=concurrency,
    )
    with loading("Evaluating..."):
        batch_runner.perform()

    # TODO: Remove before launch
    with loading("Optimizing…"):
        rules_and_tips = generate_rules_and_tips(context=context, model=model)

    # ------------------------------------------------------------------
    # Rule placement
    # ------------------------------------------------------------------
    with loading("Generating code modifications…"):
        code_mods = RuleLocator(rules_and_tips, model=model).perform()

    # ------------------------------------------------------------------
    # Display placements & save to markdown
    # ------------------------------------------------------------------
    if not code_mods:
        typer.echo("⚠️  No rule placements found.")
        raise typer.Exit(code=1)

    typer.echo("\n📋 Optimization results:\n")
    # Build the structured output
    md_lines = ["# Optimization Results\n"]

    # Console output and markdown content
    for code_mod in code_mods:
        file = code_mod["target"]["file_path"]
        typer.echo("")
        typer.echo(f"File: {file} ".ljust(100, "="))
        typer.echo("Source:")
        typer.echo(f"```python\n{code_mod['target']['source_code']}\n```")
        typer.echo("Optimizations:")
        rich.print_json(data=code_mod["mods"])

        md_lines.append(f"## File: {file}\n")
        md_lines.append("Source:")
        md_lines.append(f"```python\n{code_mod['target']['source_code']}\n```")
        md_lines.append("Optimizations:")
        if code_mod["mods"].get("always"):
            md_lines.append("<always>")
            for i, rule in enumerate(code_mod["mods"]["always"]):
                md_lines.append(f"  {i + 1}. {rule}")
            md_lines.append("</always>")
        if code_mod["mods"].get("never"):
            md_lines.append("<never>")
            for i, rule in enumerate(code_mod["mods"]["never"]):
                md_lines.append(f"  {i + 1}. {rule}")
            md_lines.append("</never>")
        if code_mod["mods"].get("tips"):
            md_lines.append("<tips>")
            for i, rule in enumerate(code_mod["mods"]["tips"]):
                md_lines.append(f"  {i + 1}. {rule}")
            md_lines.append("</tips>")
        md_lines.append("\n")

    report_path = Path(f"optimization_{datetime.now():%Y%m%d_%H%M}.md")
    report_path.write_text("\n".join(md_lines))
    typer.echo(f"\n📝 Optimization report saved to: {report_path}\n")


cli = typer.Typer(rich_markup_mode="markdown")


@cli.command()
def main(
    model: str = "openai/gpt-4.1",
    examples: int = 32,
    seed: int = 42,
    concurrency: int = 16,
):  # noqa: C901 – the CLI can be a bit long
    """Interactive `aiai` CLI as described in `aiai/cli/README.md`."""

    # Early imports kept local to speed up `python -m aiai` startup.
    load_dotenv()

    # Defaults for synthetic data generation
    typer.secho("\n🚀 Welcome to aiai! 🤖\n", fg=typer.colors.BRIGHT_CYAN, bold=True)

    # ------------------------------------------------------------------
    # 1️⃣  Agent selection
    # ------------------------------------------------------------------
    typer.secho("What would you like to optimize?\n (1) Outbound email agent (Demo)\n (2) My own agent")
    choice = typer.prompt("Enter your choice (1 or 2)", type=int)

    if choice == 1:
        typer.echo("🔑 The demo agent requires an OpenAI API key...")
        if not typer.confirm("Have you added an `OPENAI_API_KEY` to the `.env` file?", default=False):
            raise typer.Exit(code=1)

        # Path to the pre‑configured demo entrypoint
        # NOTE: This path needs adjustment when run from cli/app.py
        # Let's assume the script is run from the project root for now,
        # or we pass the root path explicitly.
        # For simplicity, using a relative path from expected root execution
        entrypoint = Path("aiai/examples/crewai/entrypoint.py").resolve()

    elif choice == 2:
        typer.secho(
            dedent(
                """\

                To optimize your own agent, we need an entrypoint.py file.
                This file must have a `def main(example=None)` function that
                runs your agent with the provided example.

                Here's an example of what a minimal entrypoint.py file looks like:

                ```python
                def main(example=None):
                    crew = get_crewai_agent()
                    example = example or ... # add your own default example here
                    result = crew.kickoff({"input": example})
                    return result.raw
                ```
                """
            )
        )

        entrypoint = Path(typer.prompt("\nPath to entrypoint")).expanduser().resolve()
        if not entrypoint.exists():
            typer.secho(f"❌ Entrypoint file not found: {entrypoint}", fg=typer.colors.RED)
            raise typer.Exit(code=1)
    else:
        typer.secho("❌ Invalid choice. Exiting.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # ------------------------------------------------------------------
    # 2️⃣  Entrypoint validation
    # ------------------------------------------------------------------
    try:
        _validate_entrypoint(entrypoint)
    except Exception as exc:  # noqa: BLE001 – show raw error to user
        typer.secho(f"❌ Failed to run the entrypoint. Error details:\n{exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # ------------------------------------------------------------------
    # 3️⃣  Analysis setup
    # ------------------------------------------------------------------
    # setup_django() # Now called in aiai/__init__.py
    reset_db()

    # ------------------------------------------------------------------
    # 4️⃣  Code analysis ➜ Dependency graph
    # ------------------------------------------------------------------
    with loading("Analyzing code…"):
        opt_ctx = analyze_code(entrypoint, model)

    # ------------------------------------------------------------------
    # 5️⃣  Evaluation criteria generation
    # ------------------------------------------------------------------
    try:
        # No need for inner import now
        with loading("Generating evals…"):
            generator = EvalGenerator(opt_ctx, model)
            rules_eval, _ = generator.perform()  # Ignore head_to_head
        typer.echo("<judge_prompt>")
        typer.echo(rules_eval.prompt)
        typer.echo("</judge_prompt>")
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
        _optimization_run(
            entrypoint,
            rules_eval,
            context=opt_ctx,
            model=model,
            examples=examples,
            seed=seed,
            concurrency=concurrency,
        )
    else:
        typer.secho(
            "⚠️  Optimisation run skipped because evaluation criteria were not generated.\n",
            fg=typer.colors.YELLOW,
        )

    typer.secho("👋 Exiting.\n", fg=typer.colors.BRIGHT_CYAN, bold=True)


# --- Typer hook --------------------------------------------------------------
if __name__ == "__main__":
    # This allows running `python -m aiai` directly
    # Set up Django FIRST when running as main script
    # setup_django() # Now called in aiai/__init__.py
    cli()
