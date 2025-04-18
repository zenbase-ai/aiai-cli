import json
import typing

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

from aiai.utils import setup_django


class DjangoSpanExporter(SpanExporter):
    def __init__(self, run_id: str, *args, **kwargs):
        setup_django()
        self.run_id = run_id
        super().__init__(*args, **kwargs)

    def export(self, spans: typing.Sequence[ReadableSpan]) -> SpanExportResult:
        from aiai.app.models import OtelSpan

        objects: list[OtelSpan] = []

        for span in spans:
            prompt = ""
            response = ""
            for event in span.events:
                if event.name == "gen_ai.content.prompt":
                    prompt = event.attributes.get("gen_ai.prompt", "")
                elif event.name == "gen_ai.content.completion":
                    response = event.attributes.get("gen_ai.completion", "")

            if prompt or response:
                objects.append(
                    OtelSpan(
                        agent_run_id=self.run_id,
                        input_data={"prompt": prompt},
                        output_data=response,
                        raw_span=json.loads(span.to_json()),
                    )
                )

        OtelSpan.objects.bulk_create(objects)

        return SpanExportResult.SUCCESS
