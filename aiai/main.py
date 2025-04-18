import os
from pathlib import Path

import typer
from dotenv import load_dotenv

from aiai.utils import setup_django


def main():
    # Load environment variables and set up Django
    load_dotenv()
    setup_django()

    typer.echo("Hello from aiai CLI!")
    # If you want to do any DB operations here:
    from aiai.app.models import OtelSpan

    log = OtelSpan.objects.create(input_data={"example": "data"}, output_data="Sample output")
    typer.echo(f"Created log with ID: {log.pk}")

    # Check if OpenAI API key is available and run the CrewAI example
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if openai_api_key:
        from aiai.logger.log_ingestor import LogIngestor

        cwd = Path(__file__).parent
        script_to_run = str(cwd / "examples/crewai_agent.py")
        typer.echo(f"Running CrewAI example: {script_to_run}")
        LogIngestor().run_script(script_to_run)
    else:
        typer.echo("Skipping CrewAI example (OPENAI_API_KEY not found in environment)")

    # Run the code analyzer on a sample file
    cwd = Path(__file__).parent
    sample_file = str(cwd / "code_analyzer/tests/sample_code.py")
    typer.echo(f"Analyzing code: {sample_file}")

    from aiai.code_analyzer import CodeAnalyzer

    # Initialize the analyzer with the appropriate language parser
    analyzer = CodeAnalyzer()

    # Analyze code starting from an entrypoint file without following imports
    graph = analyzer.analyze_from_file(sample_file, save_to_db=True)
    typer.echo(f"Code analysis complete! Found {len(graph.functions)} functions.")

    return 0


if __name__ == "__main__":
    main()
