import importlib.util
import os
import sys
import uuid

import instructor
import openlit
from dotenv import load_dotenv
from litellm import completion
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from aiai.app.models import OtelSpan
from aiai.evals import evaluate_crew_output
from aiai.logger.openlit_exporters import DjangoSpanExporter
from aiai.utils import setup_django


class LogIngestor:
    def __init__(self):
        setup_django()
        load_dotenv()
        self.provider = TracerProvider()
        trace.set_tracer_provider(self.provider)
        self.span_exporter = DjangoSpanExporter()
        trace.get_tracer_provider().add_span_processor(
            BatchSpanProcessor(self.span_exporter)
        )
        openlit.init()
        self.tracer = trace.get_tracer(__name__)

    def run_script(self, file_path: str):
        """
        Runs a Python script, captures its execution trace with OpenTelemetry,
        evaluates the output, and stores the results.

        Args:
            file_path: The absolute path to the Python script to execute.
                       The script must contain a callable 'main' function.
        """
        print(f"Starting execution of: {file_path}...")
        agent_run_id = str(uuid.uuid4())
        self.span_exporter.set_agent_run_id(agent_run_id)

        # Dynamically import and run the main function from the file_path
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for module from file: {file_path}")

        module = importlib.util.module_from_spec(spec)
        # Add the module to sys.modules BEFORE executing it
        # This ensures that relative imports within the executed script work correctly
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)

            if hasattr(module, "main") and callable(module.main):
                # Execute the main function within a span
                with self.tracer.start_as_current_span("script_execution") as span:
                    span.set_attribute("file_path", file_path)
                    span.set_attribute("agent_run_id", agent_run_id)
                    result = module.main()
                    span.set_attribute(
                        "result", str(result)
                    )  # Keep result simple for attribute

            else:
                raise AttributeError(
                    f"'main' function not found or not callable in {file_path}"
                )
        finally:
            # Clean up the temporarily added module from sys.modules
            if module_name in sys.modules:
                del sys.modules[module_name]

        # Evaluate the result after the script execution span has ended
        client = instructor.from_litellm(completion)
        success = evaluate_crew_output(result, client)

        # Create a separate record for evaluation result linked to the run
        OtelSpan.objects.create(
            agent_run_id=agent_run_id,
            input_data={
                "file_path": file_path,
                "raw_result": result,
            },  # Store raw result here
            output_data={
                "classification": success.classification,
                "reasoning": success.reasoning,
            },
            raw_span={},  # Not a direct span, but evaluation meta-data
        )
        print(f"Finished execution and evaluation for: {file_path}")
        print(f"Evaluation Result: {success.classification} - {success.reasoning}")
