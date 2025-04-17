import rich
from dotenv import load_dotenv

from aiai.utils import setup_django


async def cli():
    load_dotenv()
    setup_django()

    rich.print("Loading function info...", end=" ")
    from aiai.app.models import FunctionInfo

    fns = [fn async for fn in FunctionInfo.objects.all()]
    rich.print(f"{len(fns)} functions loaded.")
