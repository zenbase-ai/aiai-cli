import pytest

from aiai.app.models import OtelSpan
from aiai.app.settings import BASE_DIR
from aiai.logger.runner import Runner


@pytest.mark.django_db
def test_extractor():
    script_to_run = BASE_DIR / "aiai" / "examples" / "crewai_agent.py"
    logger = Runner()
    logger.run_script(script_to_run)
    assert 1 <= OtelSpan.objects.count() <= 10


@pytest.mark.django_db
def test_extractor_with_input():
    script_to_run = BASE_DIR / "aiai" / "examples" / "crewai_agent.py"
    logger = Runner()
    logger.run_script(script_to_run, input_data="hello")
    assert 1 <= OtelSpan.objects.count() <= 10
