import logging
import re
import time
from pathlib import Path

import typer

import gsrb.cli.record
from gsrb.utils.app import get_version
from gsrb.utils.logging import config_logger

logger = logging.getLogger("gsrb.cli.batch_record")


def batch_record(
    script_paths: list[Path],
    generate: bool = False,
    device: str = "emulator-5554",
) -> None:
    config_logger()
    for script_path in script_paths:
        package = script_path.name
        version = get_version(device, package)
        if version is None:
            logger.error(f"cannot get version of {package}, please check install state")
            exit(-1)
        logger.info(f"the version of {package} is {version}")
        for script in script_path.iterdir():
            if re.match(r"\d\d\.py", script.name):
                logger.info(f"record {script.name}")

                gsrb.cli.record.record(
                    script_path,
                    script.name.split(".")[0],
                    generate=generate,
                    device=device,
                )

                if generate:
                    time.sleep(60)


def main() -> None:
    typer.run(batch_record)
