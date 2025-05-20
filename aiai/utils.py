import io
import logging
import os
import sys
import threading
import time
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from contextvars import ContextVar
from itertools import cycle
from time import monotonic
from uuid import uuid4

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn
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

    # Configure logging levels based on DEBUG environment variable
    debug_mode = os.getenv("DEBUG", "False").lower() == "true"

    # Ensure a basic handler is configured, especially for debug mode
    # If DEBUG is true, set root logger level to INFO, otherwise let it be (usually WARNING by default)
    # This ensures that if specific loggers are set to INFO, they can actually output.
    if debug_mode:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    # If not in debug mode, we assume specific configurations or defaults are fine,
    # and we don't want to override a potentially more nuanced existing setup with a broad basicConfig.

    loggers_config = {
        "aiai": logging.INFO,  # Always INFO for aiai itself as per memory
        "tqdm": logging.WARNING,
        "docetl": logging.CRITICAL,
        "litellm": logging.CRITICAL,
        "openlit": logging.CRITICAL,
        "django": logging.CRITICAL,
    }

    if debug_mode:
        # In debug mode, set all specified loggers to INFO for verbosity
        for logger_name in loggers_config:
            logging.getLogger(logger_name).setLevel(logging.INFO)
            # For tqdm, INFO might be too verbose, let's keep it at WARNING or INFO based on preference.
            # For now, INFO is fine as per 'every log' request.
    else:
        # In non-debug (silent) mode, apply specific levels from memory
        for logger_name, level in loggers_config.items():
            logging.getLogger(logger_name).setLevel(level)


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


class TqdmAwareStringIO(io.StringIO):
    """A StringIO that allows tqdm output to pass through."""

    def __init__(self, original_stream=None):
        super().__init__()
        self.original_stream = original_stream

    def write(self, s):
        # If this is tqdm output (which has '\r' at the beginning),
        # write to the original stream
        if s.startswith("\r"):
            if self.original_stream:
                self.original_stream.write(s)
                self.original_stream.flush()
        else:
            super().write(s)

    def flush(self):
        if self.original_stream:
            self.original_stream.flush()
        super().flush()


@contextmanager
def silence():
    """Temporarily suppress *all* stdout / stderr output except tqdm progress bars,
    unless the DEBUG environment variable is set to 'True'."""
    debug_mode = os.getenv("DEBUG", "False").lower() == "true"

    if debug_mode:
        # In debug mode, don't suppress anything. Yield original streams.
        yield sys.stdout, sys.stderr
    else:
        # Original silence logic
        stdout = TqdmAwareStringIO(original_stream=sys.__stdout__)
        stderr = TqdmAwareStringIO(original_stream=sys.__stderr__)
        with redirect_stdout(stdout), redirect_stderr(stderr):
            yield stdout, stderr


@contextmanager
def loading(message: str, silent: bool = True, animated_emoji: bool = False):
    """Show pretty Rich spinner while silencing inner output.

    Args:
        message: Message to display
        silent: Whether to silence stdout/stderr
        animated_emoji: Whether to show an animated emoji alongside the progress message
    """
    start_at = monotonic()
    stop_animation = threading.Event()

    if animated_emoji:
        # Create and start emoji animation thread
        def emoji_animation():
            emojis = cycle(["⏳", "🔄", "🔁", "🔃", "🔄", "⌛"])
            while not stop_animation.is_set():
                emoji = next(emojis)
                print(f"\r{emoji} {message}", end="", flush=True)
                time.sleep(0.3)

        animation_thread = threading.Thread(target=emoji_animation)
        animation_thread.daemon = True
        animation_thread.start()

        try:
            if silent:
                with silence():
                    yield
            else:
                yield
        finally:
            # Stop the animation
            stop_animation.set()
            animation_thread.join(timeout=0.5)
            # Clear the animation line
            print("\r" + " " * (len(message) + 10) + "\r", end="", flush=True)
    else:
        # Original implementation with Progress
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
