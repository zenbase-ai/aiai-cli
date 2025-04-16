import typing
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

from aiai.utils import setup_django


class FileSpanExporter(SpanExporter):
    def __init__(self, *args, **kwargs):
        setup_django()
        super().__init__(*args, **kwargs)
        self.agent_run_id = None

    def set_agent_run_id(self, agent_run_id: str):
        self.agent_run_id = agent_run_id

    def export(self, spans: typing.Sequence[ReadableSpan]) -> SpanExportResult:
        from aiai.db_app.models import AgentRunLog
        for span in spans:
            prompt = ""
            response = ""
            for event in span.events:
                if event.name == "gen_ai.content.prompt":
                    prompt = event.attributes.get("gen_ai.prompt", "")
                elif event.name == "gen_ai.content.completion":
                    response = event.attributes.get("gen_ai.completion", "")

            if prompt or response:
                AgentRunLog.objects.create(
                    agent_run_id=self.agent_run_id,
                    input_data={"prompt": prompt},
                    output_data=response,
                    success={"result": True},
                )

        return SpanExportResult.SUCCESS
