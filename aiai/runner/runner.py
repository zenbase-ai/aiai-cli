from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from aiai.app.models import EvalRun
from aiai.runner.script_tracer import ScriptTracer

if TYPE_CHECKING:
    pass


@dataclass
class Runner:
    script: Path
    data: list[Any]
    eval: Callable[[Any], Any]
    concurrency: int = 16

    def perform(self):
        with ThreadPoolExecutor(max_workers=self.concurrency) as pool:
            results = pool.map(self._run_datum, self.data)
        return EvalRun.objects.bulk_create(results)

    def _run_datum(self, input_data: Any):
        with ScriptTracer(self.script) as tracer:
            run_id, output_data = tracer(input_data)
            reward = self.eval(output_data)

        return EvalRun(
            agent_run_id=run_id,
            input_data=input_data,
            output_data=output_data,
            reward=reward,
        )
