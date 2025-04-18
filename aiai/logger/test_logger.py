import pytest

from aiai.app.models import OtelSpan
from aiai.app.settings import BASE_DIR
from aiai.logger.log_ingestor import LogIngestor


@pytest.mark.django_db
def test_extractor():
    script_to_run = BASE_DIR / "aiai" / "examples" / "crewai_agent.py"
    logger = LogIngestor()
    logger.run_script(script_to_run)
    assert 1 <= OtelSpan.objects.count() <= 10
