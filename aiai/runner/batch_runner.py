import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import tqdm

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
            # Submit all tasks and get futures
            futures = [pool.submit(self.__call__, item) for item in self.data]

            # Create progress bar
            progress_bar = tqdm.tqdm(
                total=len(futures),
                desc="Processing inputs",
                unit="input",
                file=sys.stdout,
                dynamic_ncols=True,
                position=0,
                leave=True,
            )

            # Process completed futures as they finish
            results = []
            for future in as_completed(futures):
                results.append(future.result())
                progress_bar.update(1)

            progress_bar.close()

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
