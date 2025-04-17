import os
from textwrap import dedent
from typing import TYPE_CHECKING

import django
from django.core.management import call_command

if TYPE_CHECKING:
    from aiai.evals import FunctionInfo


def setup_django():
    # Point to your minimal_django settings
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aiai.app.settings")
    django.setup()
    # Run migrations silently
    call_command("migrate", verbosity=0, interactive=False)


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
