from pathlib import Path
import typer


from aiai.utils import setup_django


def main():
    typer.echo("Hello from aiai CLI!")
    # If you want to do any DB operations here:
    from aiai.app.models import OtelSpan

    log = OtelSpan.objects.create(
        input_data={"example": "data"}, output_data="Sample output", success=True
    )
    typer.echo(f"Created log with ID: {log.pk}")


if __name__ == "__main__":
    setup_django()
    from aiai.log_ingestor import run

    cwd = Path(__file__).parent
    script_to_run = str(cwd / "examples/crewai_agent.py")

    run(script_to_run)

    from aiai.code_analyzer import CodeAnalyzer

    # Initialize the analyzer with the appropriate language parser
    analyzer = CodeAnalyzer()

    # Analyze code starting from an entrypoint file without following imports
    graph = analyzer.analyze_from_file(script_to_run, save_to_db=True)
