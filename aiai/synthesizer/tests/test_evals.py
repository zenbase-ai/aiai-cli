import pytest

from aiai.app.models import FunctionInfo, SyntheticEval
from aiai.synthesizer.evals import AbstractEval, EvalGenerator, HeadToHeadEval, RulesEval


def test_eval_generator_rules(mock_function_info: list[FunctionInfo], mock_examples: list[str]):
    generator = EvalGenerator(prompt_model="openai/gpt-4.1-mini")
    eval = generator.rules(mock_function_info, mock_examples)
    assert isinstance(eval, RulesEval)
    assert "sales email" in str(eval)
    assert_eval_fields(eval)


def test_eval_generator_head_to_head(mock_function_info: list[FunctionInfo], mock_examples: list[str]):
    generator = EvalGenerator(prompt_model="openai/gpt-4.1-mini")
    eval = generator.head_to_head(mock_function_info, mock_examples)
    assert isinstance(eval, HeadToHeadEval)
    assert "Zenbase" in str(eval)
    assert "sales email" in str(eval)
    assert_eval_fields(eval)


def assert_eval_fields(eval: AbstractEval):
    assert eval.always
    assert eval.never
    assert eval.tips
    assert eval.context
    assert eval.instructions
    assert "<context>" in str(eval)
    assert "<instructions>" in str(eval)
    assert "<always>" in str(eval)
    assert "<never>" in str(eval)
    assert "<tips>" in str(eval)


@pytest.mark.django_db
def test_eval_generator_perform(mock_function_info: list[FunctionInfo]):
    FunctionInfo.objects.bulk_create(mock_function_info)

    generator = EvalGenerator(prompt_model="openai/gpt-4.1-mini")
    generator.perform()
    evals = list(SyntheticEval.objects.all())
    assert len(evals) == 2
    assert any(e.kind == "rules" for e in evals)
    assert any(e.kind == "head_to_head" for e in evals)
