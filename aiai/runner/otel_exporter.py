import typing
from datetime import datetime

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from pytz import UTC


class DjangoSpanExporter(SpanExporter):
    def export(self, captured_spans: typing.Sequence[ReadableSpan]) -> SpanExportResult:
        from aiai.app.models import OtelSpan

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
                    trace_id=str(span.context.trace_id),
                    span_id=str(span.context.span_id),
                    start_time=timestamp_to_datetime(span.start_time),
                    end_time=timestamp_to_datetime(span.end_time),
                    attributes=dict(span.attributes),
                    prompt=prompt,
                    completion=completion,
                )
            )

        OtelSpan.objects.bulk_create(models)

        return SpanExportResult.SUCCESS


def timestamp_to_datetime(timestamp: int) -> datetime:
    return datetime.fromtimestamp(timestamp / 1e9, UTC)
