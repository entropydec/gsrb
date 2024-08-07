from pathlib import Path
from typing import Annotated

import typer

from gsrb.common.step import load_testcase
from gsrb.repair import Repair
from gsrb.utils.logging import config_logger


def repair(
    record_path: Annotated[
        Path, typer.Argument(exists=True, file_okay=False, resolve_path=True)
    ],
    id: str,
    generate: bool = False,
    device: str = "emulator-5556",
) -> None:
    config_logger()
    package = record_path.name
    if generate:
        input = record_path / f"{id}.generate.zip"
        output = Path(f"data/repair/{package}/{id}.repaired.generate.py")

    else:
        input = record_path / f"{id}.zip"
        output = Path(f"data/repair/{package}/{id}.repaired.py")

    testcase, pretest = load_testcase(input, generate)

    r = Repair(
        testcase,
        package,
        output,
        device,
        pretest=pretest,
        optimize_explore=False,
        remove_assertion=False,
    )
    r.repair()


def main() -> None:
    typer.run(repair)
