import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

import openlit
from opentelemetry import trace
from opentelemetry._events import NoOpEventLogger
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from aiai.runner.otel_exporter import DjangoSpanExporter


class ScriptTracer:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.module_name = file_path.stem

    def __enter__(self) -> "ScriptTracer":
        self.run_id = uuid4().hex
        self.provider = TracerProvider()
        self.exporter = DjangoSpanExporter(self.run_id)
        self.provider.add_span_processor(BatchSpanProcessor(self.exporter))
        trace.set_tracer_provider(self.provider)

        self.tracer = self.provider.get_tracer(__name__)
        openlit.init(
            environment="dev",
            tracer=self.tracer,
            event_logger=NoOpEventLogger(name="noop"),
            disable_metrics=True,
        )

        module_name = self.file_path.stem
        spec = importlib.util.spec_from_file_location(module_name, self.file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for module from file: {self.file_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[self.module_name] = module

        spec.loader.exec_module(module)

        if not hasattr(module, "main") or not callable(module.main):
            raise AttributeError(f"'main' function not found or not callable in {self.file_path}")

        self.module = module
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.module_name in sys.modules:
            del sys.modules[self.module_name]
        self.provider.force_flush()

    def __call__(self, input_data=None, span_decorator: Callable[[Any], dict] | None = None) -> tuple[str, Any]:
        assert self.run_id is not None

        with self.tracer.start_as_current_span("script_execution") as span:
            span.set_attribute("file_path", str(self.file_path))
            span.set_attribute("agent_run_id", self.run_id)

            # Support both `main()` and `main(input_data)` signatures.
            try:
                sig = inspect.signature(self.module.main)
                if len(sig.parameters) == 0:
                    result = self.module.main()
                else:
                    result = self.module.main(input_data)
            except ValueError:
                # Fallback if signature cannot be inspected.
                result = self.module.main(input_data)
            # Keep result simple for attribute
            span.set_attribute("result", str(result))
            if span_decorator:
                for k, v in span_decorator(result).items():
                    span.set_attribute(k, v)

        return self.run_id, result
