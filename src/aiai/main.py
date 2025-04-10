# src/aiai/main.py

import typer
import os
import django
from django.core.management import call_command
import openlit

def setup_django():
    # Point to your minimal_django settings
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aiai.minimal_django.settings")
    django.setup()
    # Run migrations silently
    call_command('migrate', verbosity=0, interactive=False)

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
