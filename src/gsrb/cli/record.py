import logging
from pathlib import Path
from typing import Annotated, Optional

import typer

import gsrb.record.manager
from gsrb.utils.logging import config_logger

logger = logging.getLogger(__name__)


def record(
    script_path: Annotated[
        Path, typer.Argument(exists=True, file_okay=False, resolve_path=True)
    ],
    id: str,
    rewrite: Optional[Path] = None,
    generate: bool = False,
    device: str = "emulator-5554",
) -> None:
    config_logger()
    input = script_path / f"{id}.py"
    package = script_path.name
    if generate:
        output = Path(f"data/record/{package}/{id}.generate.zip")
    else:
        output = Path(f"data/record/{package}/{id}.zip")
    try:
        script = input.read_text(encoding="utf-8")
    except IOError:
        logger.exception("read script failed")
        exit(-1)
    try:
        pretest_path = input.parent / "pretest.py"
        pretest = pretest_path.read_text(encoding="utf-8")
        logger.info(f"load pretest from {pretest_path.resolve()}")
    except IOError:
        pretest = None
        pass

    gsrb.record.manager.record(
        package, script, output, device, pretest, rewrite, generate
    )


def main() -> None:
    typer.run(record)
