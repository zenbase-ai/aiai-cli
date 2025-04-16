# src/aiai/db_app/tests.py
import pytest
from aiai.db_app.models import AgentRunLog

@pytest.mark.django_db
def test_create_log():
    """Test creation of an AgentRunLog entry."""
    log = AgentRunLog.objects.create(
        input_data={"user": "TestUser"},
        output_data="Hello, world!",
        success=True
    )
    assert log.pk is not None
    assert log.success is True
