import logging
from pathlib import Path
from typing import Annotated

import typer

import gsrb.record.manager
import gsrb.repair.repair
from gsrb.common.step import load_testcase
from gsrb.utils.logging import config_logger

logger = logging.getLogger(__name__)

app = typer.Typer()


@app.command()
def record(
    package: str,
    script: Annotated[
        Path, typer.Argument(exists=True, dir_okay=False, resolve_path=True)
    ],
    device: str = "emulator-5554",
    draw: bool = False,
) -> None:
    config_logger()
    output = script.parent / script.name.replace(".py", ".zip")
    script_content = script.read_text(encoding="utf-8")
    pretest = script.parent / "pretest.py"
    pretest_content = None
    if pretest.exists():
        pretest_content = pretest.read_text(encoding="utf-8")

    gsrb.record.manager.record(
        package, script_content, output, device, pretest_content, draw=draw
    )


@app.command()
def repair(
    package: str,
    record: Annotated[
        Path, typer.Argument(exists=True, dir_okay=False, resolve_path=True)
    ],
    device: str = "emulator-5556",
) -> None:
    config_logger()
    output = record.parent / record.name.replace(".zip", ".repaired.py")
    verbose_output = output.parent / output.name.replace(".py", ".zip")
    testcase, pretest = load_testcase(record)
    r = gsrb.repair.repair.Repair(
        testcase,
        package,
        output,
        device=device,
        pretest=pretest,
        verbose_output=verbose_output,
    )
    r.repair()


def main() -> None:
    app()
