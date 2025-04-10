import json
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult


class FileSpanExporter(SpanExporter):
    def export(self, spans: list[ReadableSpan]) -> SpanExportResult:
        for span in spans:
            prompt = ""
            response = ""
            # Look for prompt and response in span events
            for event in span.events:
                if event.name == "gen_ai.content.prompt":
                    prompt = event.attributes.get("gen_ai.prompt", "")
                elif event.name == "gen_ai.content.completion":
                    response = event.attributes.get("gen_ai.completion", "")
            if prompt or response: # Only write if we found something
                output_data = {"input_prompt": prompt, "output_response": response}
                with open("span_output22.jsonl", "a") as f:
                    json.dump(output_data, f)
                    f.write("\n") # Add a newline to separate JSON objects (JSON Lines format)
        return SpanExportResult.SUCCESS
