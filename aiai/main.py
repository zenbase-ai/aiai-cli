import io
import json
import os
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from time import monotonic
from typing import Callable, Optional, cast

import rich
import typer
from dotenv import load_dotenv
from rich.progress import Progress, SpinnerColumn, TextColumn

from aiai.code_analyzer import CodeAnalyzer
from aiai.optimizer.contextualizer import AgentContext, generate_context
from aiai.optimizer.rule_extractor import generate_rules_and_tips
from aiai.optimizer.rule_locator import RuleLocator
from aiai.runner.batch_runner import BatchRunner
from aiai.runner.py_script_tracer import PyScriptTracer
from aiai.synthesizer.data import generate_data
from aiai.synthesizer.evals import EvalGenerator, RulesEval, SyntheticEvalRunner
from aiai.utils import log_event, log_init, reset_db, setup_django

# Use absolute imports within the package

# ---------------------------------------------------------------------------
# Utility: silence stdout/stderr and loading spinner
# ---------------------------------------------------------------------------

cwd = Path.cwd()


@contextmanager
def silence():
    """Temporarily suppress *all* stdout / stderr output (prints, progress bars, etc.)."""
    stdout, stderr = io.StringIO(), io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        yield stdout, stderr


@contextmanager
def loading(message: str, silent: bool = True):
    """Show pretty Rich spinner while silencing inner output."""
    start_at = monotonic()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description=message, total=None)
        if silent:
            with silence():
                yield
        else:
            yield
    duration = monotonic() - start_at
    typer.secho(f"✅ {message} completed in {duration:.2f}s", fg=typer.colors.GREEN)


def analyze_code(file: Path, model: str) -> AgentContext:
    from aiai.app.models import FunctionInfo

    CodeAnalyzer().analyze_from_file(file, save_to_db=True)
    source_code = json.dumps(
        {name: source for name, source in FunctionInfo.objects.values_list("name", "source_code")},
    )
    context = generate_context(source_code=source_code, model=model)
    rich.print_json(context.analysis.model_dump_json())
    return context


def group_and_sort_mods(code_mods: list[dict]) -> dict:
    """Group modifications by file and sort them by line number within each file.

    Args:
        code_mods: List of code modification dictionaries

    Returns:
        Dictionary with file paths as keys and sorted lists of modifications as values
    """
    # Group modifications by file
    file_groups = {}
    for mod in code_mods:
        file_path = mod["target"]["file_path"]
        if file_path not in file_groups:
            file_groups[file_path] = []
        file_groups[file_path].append(mod)

    # Sort each group by line number
    for file_path, mods in file_groups.items():
        mods.sort(key=lambda m: m["precise_insertion_point"].get("line_number", 0) or 0)

    return file_groups


def generate_optimization_report(code_mods: list[dict], write_to: Path):
    """Generate a markdown report from optimization results in the specified format."""
    md_lines = []

    # Group and sort modifications
    file_groups = group_and_sort_mods(code_mods)

    # Process each file
    for file_path, mods in file_groups.items():
        md_lines.append(f"# {file_path}")
        md_lines.append("")

        for mod in mods:
            line_number = mod["precise_insertion_point"].get("line_number", "?")
            rule_type = mod["rule_type"].upper()
            rule = mod["rule_content"]

            md_lines.append(f"{rule_type}")
            md_lines.append(f"{rule}")
            md_lines.append(f"{file_path}:{line_number}")
            md_lines.append("---")

        md_lines.append("---------------")
        md_lines.append("")

    # Write to file
    content = "\n".join(md_lines)
    write_to.write_text(content)
    return content


def _validate_entrypoint(entrypoint: Path):
    if not entrypoint.exists():
        typer.secho(f"❌ Entrypoint file not found: {entrypoint}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    with loading("Validating entrypoint…"):
        with PyScriptTracer(entrypoint) as tracer:
            tracer()


def _optimization_run(
    entrypoint: Path,
    data: Path | None,
    rules_eval: RulesEval | None,
    context: AgentContext,
    evaluator: str,
    optimizer: str,
    synthesizer: str,
    examples: int,
    concurrency: int,
    seed: int,
    custom_eval_fn: Optional[Callable] = None,
):
    """Run a single optimisation pass (no epochs)."""
    # Import models here, after setup_django has run
    from aiai.app.models import SyntheticDatum

    # ------------------------------------------------------------------
    # Generate synthetic data (or reuse if already present)
    # ------------------------------------------------------------------
    if data and data.exists():
        data = json.loads(data.read_text())
    else:
        data = list(SyntheticDatum.objects.all().values_list("input_data", flat=True))
        if not data:
            with loading(f"Generating {examples} synthetic inputs…"):
                data = [d.input_data for d in generate_data(context, examples, seed, model=synthesizer)]
            with (cwd / "synthetic_data.json").open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

    # Create the evaluator - either using custom function or SyntheticEvalRunner
    if custom_eval_fn:
        eval_callable = custom_eval_fn
    else:
        eval_callable = SyntheticEvalRunner(rules_eval, model=evaluator)

    batch_runner = BatchRunner(
        script=entrypoint,
        data=cast(list, data),
        eval=eval_callable,
        concurrency=concurrency,
    )
    with loading("Evaluating..."):
        eval_runs = batch_runner.perform()

    import pandas as pd

    df = pd.DataFrame([(e.trace_id, e.reward["reward"]) for e in eval_runs])
    stats = {stat: float(getattr(df[1], stat)()) for stat in ["min", "mean", "median", "max", "std"]}
    rich.print_json(data=stats)
    log_event("stats", **stats)

    log_event(
        "optimization",
        evaluator=evaluator,
        optimizer=optimizer,
        synthesizer=synthesizer,
        examples=examples,
    )
    with loading("Optimizing…"):
        rules_and_tips = generate_rules_and_tips(context=context, model=optimizer)

    # ------------------------------------------------------------------
    # Rule placement
    # ------------------------------------------------------------------
    with loading("Generating code modifications…"):
        code_mods = RuleLocator(rules_and_tips, model=optimizer).perform()

    # ------------------------------------------------------------------
    # Display placements & save to markdown
    # ------------------------------------------------------------------
    if not code_mods:
        typer.echo("⚠️  No rule placements found.")
        raise typer.Exit(code=1)

    typer.echo("\n📋 Optimization results:\n")

    # Group and sort modifications
    file_groups = group_and_sort_mods(code_mods)

    # Console output in requested format
    for file_path, mods in file_groups.items():
        typer.echo(f"# {file_path}")
        typer.echo("")

        for mod in mods:
            line_number = mod["precise_insertion_point"].get("line_number", "?")
            rule_type = mod["rule_type"].upper()
            rule = mod["rule_content"]

            typer.echo(f"{rule_type}")
            typer.echo(f"{rule}")
            typer.echo(f"{file_path}:{line_number}")
            typer.echo("---")

        typer.echo("---------------")
        typer.echo("")

    # Generate markdown report
    report_path = cwd / f"optimization_{datetime.now():%Y%m%d_%H%M}.md"
    generate_optimization_report(code_mods, write_to=report_path)
    typer.echo(f"\n📝 Report saved to: {report_path}\n")


cli = typer.Typer(rich_markup_mode="markdown")


@cli.command()
def main(
    analyzer: str = "openai/o4-mini",
    evaluator: str = "openai/o4-mini",
    optimizer: str = "openai/gpt-4.1",
    synthesizer: str = "openai/gpt-4.1-nano",
    data: Path = None,
    custom_eval_file: Path = None,
    examples: int = 25,
    seed: int = 42,
    concurrency: int = 16,
):  # noqa: C901 – the CLI can be a bit long
    """Interactive `aiai` CLI as described in `aiai/cli/README.md`.

    You can provide custom data with --data and a custom evaluation function with --custom-eval-file.
    The custom evaluation file should contain an 'main' function that takes agent output and returns a reward dict.
    """
    if examples > 25:
        typer.secho(
            "⚠️  Maximum number of synthetic examples is 25. Setting to 25.\n",
            fg=typer.colors.YELLOW,
        )
        examples = 25

    load_dotenv()

    typer.secho("\n🚀 Welcome to aiai! 🤖\n", fg=typer.colors.BRIGHT_CYAN, bold=True)
    log_init()

    # ------------------------------------------------------------------
    # 1️⃣  Agent selection
    # ------------------------------------------------------------------
    typer.secho("What would you like to optimize?\n (1) Outbound email agent (Demo)\n (2) My own agent")
    choice = typer.prompt("Enter your choice (1 or 2)", type=int)

    if choice not in (1, 2):
        typer.secho("❌ Invalid choice. Exiting.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if choice == 1:
        if not os.getenv("OPENAI_API_KEY"):
            typer.echo("🔑 The demo agent requires an OpenAI API key...")
            if not typer.confirm("Have you added an `OPENAI_API_KEY` to the `.env` file?", default=False):
                raise typer.Exit(code=1)

        # Path to the pre‑configured demo entrypoint
        # NOTE: This path needs adjustment when run from cli/app.py
        # Let's assume the script is run from the project root for now,
        # or we pass the root path explicitly.
        # For simplicity, using a relative path from expected root execution
        log_event("demo")
        entrypoint = (Path(__file__).parent / "examples/crewai_agent.py").resolve()

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

        log_event(
            "custom",
            analyzer=analyzer,
            evaluator=evaluator,
            optimizer=optimizer,
            synthesizer=synthesizer,
            data=str(data),
            custom_eval_file=str(custom_eval_file) if custom_eval_file else None,
            examples=examples,
            seed=seed,
            concurrency=concurrency,
        )
        entrypoint = Path(typer.prompt("\nPath to entrypoint")).expanduser().resolve()

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
    setup_django()
    reset_db()

    # ------------------------------------------------------------------
    # 4️⃣  Code analysis ➜ Dependency graph
    # ------------------------------------------------------------------
    with loading("Analyzing code…"):
        opt_ctx = analyze_code(entrypoint, analyzer)
    typer.echo(opt_ctx.analysis.what)
    log_event(
        "agent_context",
        analysis=opt_ctx.analysis.model_dump_json(),
        prompts=opt_ctx.optimizer_prompts.model_dump_json(),
    )

    # ------------------------------------------------------------------
    # 5️⃣  Evaluation criteria generation or loading
    # ------------------------------------------------------------------
    rules_eval = None
    custom_eval_fn = None

    try:
        if custom_eval_file and custom_eval_file.exists():
            typer.echo(f"Using custom evaluation file: {custom_eval_file}")
            # Import the custom evaluation module
            import importlib.util
            import sys

            module_name = custom_eval_file.stem
            spec = importlib.util.spec_from_file_location(module_name, custom_eval_file)
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load custom eval file: {custom_eval_file}")

            custom_eval_module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = custom_eval_module
            spec.loader.exec_module(custom_eval_module)

            # Check if the module has a main function
            if hasattr(custom_eval_module, "main"):
                custom_eval_fn = custom_eval_module.main
                typer.echo("Custom evaluation function 'main' loaded successfully.")
            else:
                typer.secho(
                    "⚠️  Custom eval file must contain a 'main' function.\n",
                    fg=typer.colors.YELLOW,
                )
        else:
            # No need for inner import now
            with loading("Generating evals…"):
                generator = EvalGenerator(opt_ctx, evaluator)
                rules_eval, _ = generator.perform()  # Ignore head_to_head
            typer.echo(rules_eval.prompt.strip())
    except Exception as exc:  # noqa: BLE001 – non‑critical failure
        typer.secho(
            f"⚠️  Skipped evaluation criteria generation due to error: {exc}\n",
            fg=typer.colors.YELLOW,
        )
        rules_eval = None
        custom_eval_fn = None

    # ------------------------------------------------------------------
    # 6️⃣  Optimization run
    # ------------------------------------------------------------------
    if rules_eval or custom_eval_fn:
        _optimization_run(
            entrypoint,
            data=data,
            rules_eval=rules_eval,
            context=opt_ctx,
            evaluator=evaluator,
            optimizer=optimizer,
            synthesizer=synthesizer,
            examples=examples,
            seed=seed,
            concurrency=concurrency,
            custom_eval_fn=custom_eval_fn,
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
