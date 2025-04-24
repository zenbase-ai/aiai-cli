import pytest

from aiai.app.models import SyntheticEval
from aiai.optimizer.contextualizer import AgentContext
from aiai.synthesizer.evals import EvalGenerator, SyntheticEvalRunner


@pytest.fixture(scope="module")
def agent_context() -> AgentContext:
    # Create a mock AgentContext with necessary attributes
    return AgentContext(
        source_code="print('Hello, world!')",
        analysis=type(
            "obj",
            (object,),
            {
                "expert_persona": "You are a sales expert.",
                "what": "Generate professional sales emails",
                "how": "Use persuasive language and clear call to actions",
            },
        ),
        optimizer_prompts=type(
            "obj",
            (object,),
            {},
        ),
    )


@pytest.mark.django_db
def test_eval_generator(agent_context: AgentContext, mock_examples: list[str]):
    generator = EvalGenerator(agent_context=agent_context, model="openai/gpt-4.1-mini")
    rules_eval, head_to_head_eval = generator.perform(mock_examples)
    assert "sales email" in rules_eval.prompt
    assert "sales email" in head_to_head_eval.prompt
    assert rules_eval is not None
    assert head_to_head_eval is not None
    assert rules_eval.kind == "rules"
    assert head_to_head_eval.kind == "head_to_head"
    assert rules_eval.prompt is not None
    assert head_to_head_eval.prompt is not None
    assert SyntheticEval.objects.count() == 2

    runner = SyntheticEvalRunner(rules_eval)
    result = runner("Hello, world!")
    assert result is not None
    assert result["reward"] is not None
    assert result["reasoning"] is not None
    assert result["result"] is not None

    runner = SyntheticEvalRunner(head_to_head_eval)
    result = runner("Hello, world!, Hello beautiful world!")
    assert result is not None
    assert result["reward"] is not None
    assert result["reasoning"] is not None
    assert result["result"] is not None
