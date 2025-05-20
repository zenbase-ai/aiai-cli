import io
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
    """Temporarily suppress *all* stdout / stderr output except tqdm progress bars."""
    stdout = TqdmAwareStringIO(original_stream=sys.stdout)
    stderr = TqdmAwareStringIO(original_stream=sys.stderr)
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

def group_and_sort_mods(code_mods: list[dict]) -> dict:
    """Group modifications by function and sort them by line number and rule_type.

    Args:
        code_mods: List of code modification dictionaries

    Returns:
        Dictionary with function IDs as keys and sorted lists of modifications as values
    """
    # Import needed model
    setup_django()
    from aiai.app.models import FunctionInfo
    
    # Group modifications by function
    function_groups = {}
    function_not_found = []
    
    for mod in code_mods:
        file_path = mod["target"]["file_path"]
        line_number = mod["precise_insertion_point"].get("line_number", 0) or 0
        
        # Find the function this modification belongs to
        containing_function = FunctionInfo.objects.filter(
            file_path=file_path,
            line_start__lte=line_number,
            line_end__gte=line_number
        ).first()
        
        if containing_function:
            function_id = containing_function.id
            if function_id not in function_groups:
                function_groups[function_id] = []
            function_groups[function_id].append(mod)
        else:
            # Handle modifications that don't belong to any known function
            function_not_found.append(mod)
    
    # Sort each group by line number and then by rule_type
    for function_id, mods in function_groups.items():
        # First sort by line number
        mods.sort(key=lambda m: m["precise_insertion_point"].get("line_number", 0) or 0)
        # Then stable sort by rule_type if it exists
        if mods and "rule_type" in mods[0]:
            mods.sort(key=lambda m: m.get("rule_type", ""), reverse=False)
    
    # Add modifications that couldn't be assigned to a function
    if function_not_found:
        function_groups["no_function"] = sorted(
            function_not_found, 
            key=lambda m: (m["target"]["file_path"], m["precise_insertion_point"].get("line_number", 0) or 0)
        )
    
    return function_groups
