import importlib.util
import inspect
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

import openlit
from opentelemetry import trace
from opentelemetry._events import NoOpEventLogger
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from aiai.runner.otel_exporter import DjangoSpanExporter


@dataclass
class PyScriptTracer:
    file_path: Path

    def __enter__(self) -> "PyScriptTracer":
        self.module_name = self.file_path.stem
        self.provider = TracerProvider()
        self.provider.add_span_processor(BatchSpanProcessor(DjangoSpanExporter()))
        trace.set_tracer_provider(self.provider)

        self.tracer = self.provider.get_tracer(__name__)
        openlit.init(
            environment="aiai",
            tracer=self.tracer,
            event_logger=NoOpEventLogger(name="noop"),
            disable_metrics=True,
        )

        spec = importlib.util.spec_from_file_location(self.module_name, self.file_path)
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

    def __call__(self, input_data=None, span_decorator: Optional[Callable[[Any], dict]] = None) -> tuple[str, Any]:
        with self.tracer.start_as_current_span("script_execution") as span:
            span.set_attribute("file_path", str(self.file_path))

            # Support both `main()` and `main(input_data)` signatures.
            fn = self.module.main
            try:
                sig = inspect.signature(fn)
                result = fn() if len(sig.parameters) == 0 else fn(input_data)
            except ValueError:
                # Fallback if signature cannot be inspected.
                result = fn(input_data)
            # Keep result simple for attribute
            span.set_attribute("result", str(result))
            if span_decorator:
                for k, v in span_decorator(result).items():
                    span.set_attribute(k, v)

            trace_id = span.get_span_context().trace_id

        return trace_id, result
