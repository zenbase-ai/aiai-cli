from textwrap import dedent
from typing import TYPE_CHECKING

import litellm

from aiai.optimizer.contextualizer import AgentContext
from aiai.synthesizer.utils import get_examples

if TYPE_CHECKING:
    from aiai.app.models import SyntheticDatum


def generate_data(
    agent_context: AgentContext,
    count: int,
    seed: int,
    examples: list | None = None,
    model: str = "openai/gpt-4.1-mini",
    save_to_db: bool = True,
) -> list["SyntheticDatum"]:
    from aiai.app.models import FunctionInfo, SyntheticDatum

    assert count <= 25
    examples = examples or get_examples(list(FunctionInfo.objects.all()))

    response = litellm.completion(
        model=model,
        messages=[
            {
                "role": "system",
                "content": dedent(
                    f"""\
                    <instructions>
                        {agent_context.analysis.expert_persona}

                        {agent_context.optimizer_prompts.synthetic_data}
                    </instructions>

                    <examples>
                        {examples}
                    </examples>
                    """
                ),
            }
        ],
        temperature=1,
        n=count,
        seed=seed,
    )
    objects = [SyntheticDatum(input_data=r.message.content) for r in response.choices]
    if not save_to_db:
        return objects
    return SyntheticDatum.objects.bulk_create(objects)
