import pytest

from aiai.app.models import FunctionInfo, SyntheticEval
from aiai.synthesizer.evals import EvalGenerator, HeadToHeadEval, RulesEval, SyntheticEvalRunner


@pytest.fixture(scope="module")
def rules_eval(mock_function_info: list[FunctionInfo], mock_examples: list[str]) -> RulesEval:
    generator = EvalGenerator(prompt_model="openai/gpt-4.1-nano")
    rules_eval = generator.rules(mock_function_info, mock_examples)
    return rules_eval


@pytest.fixture(scope="module")
def head_to_head_eval(mock_function_info: list[FunctionInfo], mock_examples: list[str]) -> HeadToHeadEval:
    generator = EvalGenerator(prompt_model="openai/gpt-4.1-nano")
    head_to_head_eval = generator.head_to_head(mock_function_info, mock_examples)
    return head_to_head_eval


def test_eval_generator_rules(rules_eval: RulesEval):
    assert "sales email" in str(rules_eval)


def test_eval_generator_head_to_head(head_to_head_eval: HeadToHeadEval):
    assert "Zenbase" in str(head_to_head_eval)
    assert "sales email" in str(head_to_head_eval)


@pytest.mark.django_db
def test_eval_generator_perform(mock_function_info: list[FunctionInfo], mock_examples: list[str]):
    generator = EvalGenerator(prompt_model="openai/gpt-4.1-nano")
    rules_eval, head_to_head_eval = generator.perform(mock_function_info, mock_examples)
    assert rules_eval is not None
    assert head_to_head_eval is not None
    assert rules_eval.kind == "rules"
    assert head_to_head_eval.kind == "head_to_head"
    assert rules_eval.prompt is not None
    assert head_to_head_eval.prompt is not None
    assert SyntheticEval.objects.count() == 2


def test_eval_runner_rules_eval(rules_eval: RulesEval):
    runner = SyntheticEvalRunner(rules_eval.to_db_model())
    result = runner("Hello, world!")
    assert result is not None
    assert result["reward"] is not None
    assert result["reasoning"] is not None
    assert result["result"] is not None


def test_eval_runner_head_to_head_eval(head_to_head_eval: HeadToHeadEval):
    runner = SyntheticEvalRunner(head_to_head_eval.to_db_model())
    result = runner("A: Hello, world!, B: Hello beautiful world!")
    assert result is not None
    assert result["reasoning"] is not None
    assert result["result"] is not None
    assert result["reward"] in [0.0, 0.5, 1.0]
