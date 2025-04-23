from pathlib import Path
from textwrap import dedent

import pytest

from aiai.app.models import EvalRun, OtelSpan
from aiai.runner import BatchRunner


@pytest.fixture
def crewai_entrypoint() -> Path:
    return Path(__file__).parent.parent.parent / "examples" / "crewai_agent.py"


@pytest.mark.django_db
def test_runner(crewai_entrypoint: Path):
    example = [
        dedent(
            """\
            Jessica Collins, CTO at FinOptima, a mid-sized fintech startup, struggles
            with balancing model selection trade-offs, managing complex versioning of
            multiple LLMs in fraud detection pipelines, latency, and cost-per-token
            ratios during peak times.
            """
        )
    ]
    runner = BatchRunner(
        script=crewai_entrypoint,
        data=[example],
        eval=lambda _: {"reward": 0.42, "reason": "Jessica liked the email"},
        concurrency=1,
    )
    runner.perform()

    assert 1 <= OtelSpan.objects.count() <= 10
    runs = list(EvalRun.objects.all())
    assert len(runs) == 1
    assert runs[0].reward == "{'reward': 0.42, 'reason': 'Jessica liked the email'}"
