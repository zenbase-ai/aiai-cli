import os
from contextvars import ContextVar
from uuid import uuid4

from scarf import ScarfEventLogger

event_logger = ScarfEventLogger(endpoint_url="https://zenbase.gateway.scarf.sh/events/aiai-cli")
_run_id = ContextVar("run_id", default=None)


def log_init():
    import platform

    _run_id.set(uuid4().hex)
    log_event(
        "platform",
        platform=platform.system(),
        python_version=platform.python_version(),
        machine=platform.machine(),
    )


def log_event(event: str, **properties):
    properties.setdefault("event", event)
    run_id = _run_id.get()
    assert run_id is not None, "run_id is not set"
    properties.setdefault("run_id", run_id)
    event_logger.log_event(properties)


def reset_db():
    from aiai.app.models import EvalRun, FunctionInfo, OtelSpan, SyntheticDatum, SyntheticEval

    FunctionInfo.objects.all().delete()
    OtelSpan.objects.all().delete()
    EvalRun.objects.all().delete()
    SyntheticDatum.objects.all().delete()
    SyntheticEval.objects.all().delete()


def setup_django():
    import django
    from django.core.management import call_command

    # Point to your minimal_django settings
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aiai.app.settings")
    django.setup()

    # Run migrations silently
    call_command("migrate", verbosity=0, interactive=False)
