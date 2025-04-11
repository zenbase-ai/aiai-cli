import typer

from utils import setup_django


def main():
    typer.echo("Hello from aiai CLI!")
    # If you want to do any DB operations here:
    setup_django()
    from aiai.db_app.models import AgentRunLog
    log = AgentRunLog.objects.create(
        input_data={"example": "data"},
        output_data="Sample output",
        success=True
    )
    typer.echo(f"Created log with ID: {log.pk}")

if __name__ == "__main__":
    main()
