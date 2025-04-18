from unittest.mock import Mock, patch

import pytest

from aiai.app.models import FunctionInfo, SyntheticDatum
from aiai.synthetic.data import DataGenerator, SynPrompt


@pytest.fixture
def mock_function_info():
    return [
        FunctionInfo(
            name="test_func",
            file_path="test.py",
            line_start=1,
            line_end=5,
            signature="def test_func(arg1: str, arg2: int) -> bool",
            source_code="def test_func(arg1: str, arg2: int) -> bool:\n    return True",
            docstring="Test function docstring",
            comments=["# This is a test function"],
            string_literals=["test string"],
            variables={"arg1": "str", "arg2": "int"},
            constants={"MAX_RETRIES": 3},
        )
    ]


@pytest.fixture
def mock_examples():
    return ["example1", "example2"]


def test_data_generator_initialization():
    generator = DataGenerator(examples=5, seed=42)
    assert generator.examples == 5
    assert generator.seed == 42
    assert generator.prompt_model == "openai/o4-mini"
    assert generator.data_model == "openai/gpt-4.1-mini"


def test_data_generator_prompt(mock_function_info, mock_examples):
    generator = DataGenerator(examples=5, seed=42)

    with patch("instructor.from_litellm") as mock_instructor:
        mock_instructor.return_value.create = Mock(
            return_value=SynPrompt(prompt="test prompt", examples=["test example"])
        )

        result = generator.prompt(mock_function_info, mock_examples)
        assert isinstance(result, str)
        assert "test prompt" in result
        assert "test example" in result


def test_data_generator_data():
    generator = DataGenerator(examples=2, seed=42)

    mock_response = type(
        "Response",
        (),
        {
            "choices": [
                type(
                    "Choice", (), {"message": type("Message", (), {"content": "data1"})}
                ),
                type(
                    "Choice", (), {"message": type("Message", (), {"content": "data2"})}
                ),
            ]
        },
    )

    with patch("litellm.completion", new_callable=Mock) as mock_completion:
        mock_completion.return_value = mock_response

        result = generator.data("test prompt")
        assert len(result) == 2
        assert all(isinstance(d, SyntheticDatum) for d in result)
        assert result[0].input_data == "data1"
        assert result[1].input_data == "data2"
