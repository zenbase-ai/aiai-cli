from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from aiai.runner.py_script_tracer import PyScriptTracer


@dataclass
class BatchRunner:
    script: Path
    data: list[Any]
    eval: Callable[[Any], Any]
    concurrency: int = 32

    def perform(self):
        from aiai.app.models import EvalRun

        with ThreadPoolExecutor(max_workers=self.concurrency) as pool:
            results = pool.map(self.__call__, self.data)
        return EvalRun.objects.bulk_create(results)

    def tracer(self):
        if self.script.suffix == ".py":
            return PyScriptTracer(self.script)
        else:
            raise ValueError(f"Unsupported script type: {self.script.suffix}")

    def __call__(self, input_data: Any):
        from aiai.app.models import EvalRun

        reward = None

        with self.tracer() as tracer:
            trace_id, output_data = tracer(input_data)

        reward = self.eval(output_data)
        return EvalRun(
            trace_id=trace_id,
            input_data=input_data,
            output_data=output_data,
            reward=reward,
        )
