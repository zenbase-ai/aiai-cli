from pathlib import Path

import typer
from dotenv import load_dotenv

from aiai.utils import reset_db, setup_django


def analyze_code(file: Path):
    from aiai.code_analyzer import CodeAnalyzer

    analyzer = CodeAnalyzer()
    graph = analyzer.analyze_from_file(file, save_to_db=True)
    return graph


def capture_logs(file: Path):
    from aiai.logger.runner import Runner

    Runner().run_script(file)


cli = typer.Typer()


@cli.command(no_args_is_help=True)
def main(
    entrypoint: Path,
    data: Path = Path("./synthetic.json"),
    examples: int = 32,
    seed: int = 42,
):
    load_dotenv()
    setup_django()
    reset_db()

    typer.echo(f"Optimizing {entrypoint}...")
    typer.echo("Analyzing code...")
    graph = analyze_code(entrypoint)
    typer.echo(f"Code analysis complete! Found {len(graph.functions)} functions.")

    typer.echo("Capturing logs...")
    capture_logs(entrypoint)

    return 0


if __name__ == "__main__":
    cli()
