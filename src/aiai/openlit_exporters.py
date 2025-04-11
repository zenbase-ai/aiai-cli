import typing
import json
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

from aiai.utils import setup_django


class FileSpanExporter(SpanExporter):
    def __init__(self, *args, **kwargs):
        setup_django()
        super().__init__(*args, **kwargs)

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
                    input_data={"prompt": prompt},
                    output_data={"response": response},
                    success=True,
                )
        return SpanExportResult.SUCCESS
