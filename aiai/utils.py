import os
import django
from django.core.management import call_command


def setup_django():
    # Point to your minimal_django settings
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aiai.minimal_django.settings")
    django.setup()
    # Run migrations silently
    call_command("migrate", verbosity=0, interactive=False)
