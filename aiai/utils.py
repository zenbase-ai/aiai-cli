import os

import django
from django.core.management import call_command


def reset_db():
    from aiai.app.models import FunctionInfo, OtelSpan

    FunctionInfo.objects.all().delete()
    OtelSpan.objects.all().delete()


def setup_django():
    # Point to your minimal_django settings
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aiai.app.settings")
    django.setup()

    # Run migrations silently
    call_command("migrate", verbosity=0, interactive=False)
