import pytest

from aiai.app.models import OtelSpan
from aiai.app.settings import BASE_DIR
from aiai.runner.py_script_tracer import PyScriptTracer


@pytest.mark.django_db
def test_extractor_no_input():
    script_to_run = BASE_DIR / "aiai" / "examples" / "crewai_agent.py"
    with PyScriptTracer(script_to_run) as runner:
        runner()
    assert 1 <= OtelSpan.objects.count() <= 10


@pytest.mark.django_db
def test_extractor_with_input():
    script_to_run = BASE_DIR / "aiai" / "examples" / "crewai_agent.py"
    with PyScriptTracer(script_to_run) as runner:
        runner(input_data="fake input data")
    assert 1 <= OtelSpan.objects.count() <= 10
