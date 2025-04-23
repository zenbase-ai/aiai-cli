import pytest

from aiai.app.models import FunctionInfo, SyntheticDatum
from aiai.optimizer.contextualizer import AgentContext
from aiai.synthesizer.data import generate_data


@pytest.fixture
def mock_agent_context():
    class MockAnalysis:
        expert_persona = "You are an expert lead engineer"

    class MockPrompts:
        synthetic_data = "Generate synthetic data for testing"

    context = AgentContext(
        source_code="",
        analysis=MockAnalysis(),
        optimizer_prompts=MockPrompts(),
    )
    return context


def test_generate_data(mock_agent_context, mock_function_info, mock_examples):
    data = generate_data(
        agent_context=mock_agent_context,
        count=2,
        seed=42,
        examples=mock_examples,
        model="openai/gpt-4.1-mini",
        save_to_db=False,
    )

    assert len(data) == 2
    for d in data:
        assert isinstance(d, SyntheticDatum)
        assert d.input_data is not None


@pytest.mark.django_db
def test_generate_data_with_db(mock_agent_context, mock_function_info):
    FunctionInfo.objects.bulk_create(mock_function_info)

    data = generate_data(
        agent_context=mock_agent_context,
        count=2,
        seed=42,
        model="openai/gpt-4.1-mini",
    )

    assert isinstance(data, list)
    assert len(data) == 2
    for d in data:
        assert isinstance(d, SyntheticDatum)
        assert d.input_data is not None

    assert SyntheticDatum.objects.count() == 2
