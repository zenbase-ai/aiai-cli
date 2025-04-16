import uuid
import sys
import importlib.util
import os
from pathlib import Path

from dotenv import load_dotenv
import instructor
from litellm import completion
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
import openlit

from aiai.evals import evaluate_crew_output
from aiai.openlit_exporters import FileSpanExporter
from aiai.utils import setup_django


load_dotenv()
provider = TracerProvider()
trace.set_tracer_provider(provider)
span_exporter = FileSpanExporter()
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(span_exporter))
openlit.init()
tracer = trace.get_tracer(__name__)


def run(file_path):
    print(f"Starting execution of: {file_path}...")
    agent_run_id = str(uuid.uuid4())
    span_exporter.set_agent_run_id(agent_run_id)

    # Dynamically import and run the main function from the file_path
    module_name = os.path.splitext(os.path.basename(file_path))[0]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for module from file: {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    if hasattr(module, "main") and callable(module.main):
        result = module.main()
    else:
        raise AttributeError(
            f"'main' function not found or not callable in {file_path}"
        )

    from aiai.db_app.models import AgentRunLog

    client = instructor.from_litellm(completion)
    success = evaluate_crew_output(result, client)
    AgentRunLog.objects.create(
        agent_run_id=agent_run_id,
        input_data={"file_path": file_path},
        output_data=result,
        success={"result": success.classification, "reasoning": success.reasoning},
    )


if __name__ == "__main__":
    setup_django()
    cwd = Path(__file__).parent

    script_to_run = str(cwd / "crewai_agent.py")
    run(script_to_run)
