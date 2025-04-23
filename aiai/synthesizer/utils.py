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
