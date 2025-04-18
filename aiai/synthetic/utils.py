import re
from textwrap import dedent
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiai.app.models import FunctionInfo


def get_examples(fns: list["FunctionInfo"]) -> list[str]:
    examples: list[str] = []
    for fn in fns:
        for variable in fn.variables:
            if variable["name"] in ("example", "examples"):
                examples.append(variable["value"])
    return examples


def prepare_messages(
    sys_prompt: str,
    fns: list["FunctionInfo"],
    examples: list[str] | None = None,
) -> list[dict]:
    source_code = "\n".join([fn.source_code for fn in fns])
    source_code = dedent(
        f"""\
            Here is the source code for the agent:
            <source_code>
            {source_code}
            </source_code>
            """
    )
    examples = (
        f"Here are examples of my input data: <examples>\n{examples}\n</examples>"
        if examples
        else ""
    )
    return [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": source_code},
        *([{"role": "user", "content": examples}] if examples else []),
        {"role": "system", "content": sys_prompt},
    ]


def pascal_case_to_snake_case(
    name: str,
    pattern=re.compile(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])"),
) -> str:
    return pattern.sub("_", name).lower()
