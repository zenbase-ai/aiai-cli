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
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from tqdm import tqdm

    from aiai.app.models import FunctionInfo, SyntheticDatum

    assert 0 < count <= 25, "Count must be between 1 and 25."

    examples = examples or get_examples(list(FunctionInfo.objects.all()))

    system_message_content = dedent(
        f"""\
        <instructions>
            {agent_context.analysis.expert_persona}

            {agent_context.optimizer_prompts.synthetic_data}
        </instructions>

        <examples>
            {examples}
        </examples>
        """
    )

    base_messages = [
        {
            "role": "system",
            "content": system_message_content,
        }
    ]

    results_content: list[str] = []

    # Worker function for each thread
    def make_request_worker(thread_seed: int):
        _response = litellm.completion(
            model=model,
            messages=base_messages,
            temperature=1,
            n=1,
            seed=thread_seed,
        )
        # Check if the response structure is as expected
        if (
            _response.choices
            and len(_response.choices) > 0
            and _response.choices[0].message
            and _response.choices[0].message.content
        ):
            return _response.choices[0].message.content
        else:
            print(
                f"Warning: litellm.completion call with seed {thread_seed} returned unexpected structure or no content."
            )
            return None

    with ThreadPoolExecutor(max_workers=count) as executor:
        # Create a dictionary to map futures to their seeds for error reporting
        future_to_seed = {executor.submit(make_request_worker, seed + i): (seed + i) for i in range(count)}

        # Wrap as_completed with tqdm for a progress bar
        for future in tqdm(as_completed(future_to_seed), total=count, desc="Generating synthetic data"):
            current_seed = future_to_seed[future]
            try:
                content = future.result()  # This will raise an exception if the worker failed
                if content:
                    results_content.append(content)
            except Exception as e:
                # Log or print information about failed requests
                print(f"Warning: API request for synthetic data (seed {current_seed}) failed: {e}")

    # Create SyntheticDatum objects from successfully retrieved content
    objects = [SyntheticDatum(input_data=res_content) for res_content in results_content]

    if not objects and count > 0:
        # This indicates all 'count' requests failed or returned no usable content.
        print(f"Warning: All {count} attempts to generate synthetic data yielded no content.")

    # Save to DB or return objects, as in the original logic
    if not save_to_db:
        return objects
    return SyntheticDatum.objects.bulk_create(objects)
