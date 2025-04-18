# src/aiai/app/tests.py
import pytest

from aiai.app.models import OtelSpan


@pytest.mark.django_db
def test_create_log():
    """Test creation of an OtelSpan entry."""
    log = OtelSpan.objects.create(input_data={"user": "TestUser"}, output_data="Hello, world!", success=True)
    assert log.pk is not None
    assert log.success is True
