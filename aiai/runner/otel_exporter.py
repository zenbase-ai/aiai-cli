import typing
from datetime import datetime

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

from aiai.app.models import OtelSpan
from aiai.utils import setup_django


class DjangoSpanExporter(SpanExporter):
    def __init__(self, run_id: str, *args, **kwargs):
        setup_django()
        self.run_id = run_id
        super().__init__(*args, **kwargs)

    def export(self, captured_spans: typing.Sequence[ReadableSpan]) -> SpanExportResult:
        models: list[OtelSpan] = []

        for span in captured_spans:
            prompt = None
            completion = None
            for event in span.events:
                prompt = prompt or event.attributes.get("gen_ai.prompt")
                completion = completion or event.attributes.get("gen_ai.completion")

            if not prompt or not completion:
                continue

            models.append(
                OtelSpan(
                    agent_run_id=self.run_id,
                    trace_id=str(span.context.trace_id),
                    span_id=str(span.context.span_id),
                    start_time=datetime.fromtimestamp(span.start_time / 1e9),
                    end_time=datetime.fromtimestamp(span.end_time / 1e9),
                    attributes=dict(span.attributes),
                    prompt=prompt,
                    completion=completion,
                )
            )

        OtelSpan.objects.bulk_create(models)

        return SpanExportResult.SUCCESS
