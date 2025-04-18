import pytest

from aiai.app.models import FunctionInfo, SyntheticDatum
from aiai.synthesizer.data import DataGenerator


def test_data_generator_data(mock_function_info: list[FunctionInfo], mock_examples: list[str]):
    generator = DataGenerator(
        examples=2,
        seed=42,
        prompt_model="openai/gpt-4.1-mini",
        data_model="openai/gpt-4.1-mini",
    )
    assert generator.examples == 2
    assert generator.seed == 42
    assert generator.prompt_model == "openai/gpt-4.1-mini"
    assert generator.data_model == "openai/gpt-4.1-mini"

    prompt = generator.prompt(mock_function_info, mock_examples)
    assert "lead" in str(prompt)
    assert "<examples>" in str(prompt)
    assert "<instructions>" in str(prompt)

    data = generator.data(prompt)
    assert len(data) == 2
    for d in data:
        assert isinstance(d, SyntheticDatum)
        assert d.input_data is not None
        assert "LLM" in d.input_data


@pytest.mark.django_db
def test_data_generator_perform(mock_function_info: list[FunctionInfo]):
    FunctionInfo.objects.bulk_create(mock_function_info)

    generator = DataGenerator(
        examples=2,
        seed=42,
        prompt_model="openai/gpt-4.1-mini",
        data_model="openai/gpt-4.1-mini",
    )
    prompt, data = generator.perform()
    assert isinstance(prompt, str)
    assert isinstance(data, list)
    assert len(data) == 2
    for d in data:
        assert isinstance(d, SyntheticDatum)
        assert d.input_data is not None

    assert SyntheticDatum.objects.count() == 2
