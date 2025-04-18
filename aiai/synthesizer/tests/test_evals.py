from unittest.mock import Mock

import pytest

from aiai.app.models import FunctionInfo, SyntheticEval
from aiai.synthetic.evals import EvalGenerator, HeadToHeadEval, RulesEval


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


def test_rules_eval_creation():
    eval = RulesEval(
        context="test context",
        instructions="test instructions",
        always=["rule1", "rule2"],
        never=["bad1", "bad2"],
    )

    assert eval.context == "test context"
    assert eval.instructions == "test instructions"
    assert eval.always == ["rule1", "rule2"]
    assert eval.never == ["bad1", "bad2"]

    db_model = eval.to_db_model()
    assert isinstance(db_model, SyntheticEval)
    assert db_model.kind == "rules"
    assert "test context" in db_model.prompt
    assert "test instructions" in db_model.prompt


def test_head_to_head_eval_creation():
    eval = HeadToHeadEval(context="test context", instructions="test instructions", tips=["tip1", "tip2"])

    assert eval.context == "test context"
    assert eval.instructions == "test instructions"
    assert eval.tips == ["tip1", "tip2"]

    db_model = eval.to_db_model()
    assert isinstance(db_model, SyntheticEval)
    assert db_model.kind == "head_to_head"
    assert "test context" in db_model.prompt
    assert "test instructions" in db_model.prompt


def test_eval_generator_initialization():
    generator = EvalGenerator()
    assert generator.prompt_model == "openai/o4-mini"
    assert "expert AI engineer" in generator.sys_prompt


def test_eval_generator_rules(mock_function_info, mock_examples):
    generator = EvalGenerator()
    generator.lm = Mock()
    generator.lm.create = Mock(
        return_value=RulesEval(
            context="You are evaluating a Python function that processes data",
            instructions="Evaluate the function's output based on the following rules",
            always=[
                "Output must be a boolean value",
                "Function must handle all input cases",
                "Function must be well-documented",
            ],
            never=[
                "Function must not raise exceptions",
                "Function must not modify input data",
            ],
        )
    )

    result = generator.rules(mock_function_info, mock_examples)
    assert isinstance(result, RulesEval)
    assert "Python function" in result.context
    assert "Evaluate" in result.instructions
    assert len(result.always) == 3
    assert len(result.never) == 2


def test_eval_generator_head_to_head(mock_function_info, mock_examples):
    generator = EvalGenerator()
    generator.lm = Mock()
    generator.lm.create = Mock(
        return_value=HeadToHeadEval(
            context="You are comparing two implementations of a data processing function",
            instructions="Compare the outputs and determine which implementation is better",
            tips=[
                "Consider code readability",
                "Check for edge cases",
                "Evaluate performance implications",
            ],
        )
    )

    result = generator.head_to_head(mock_function_info, mock_examples)
    assert isinstance(result, HeadToHeadEval)
    assert "comparing" in result.context
    assert "Compare" in result.instructions
    assert len(result.tips) == 3
