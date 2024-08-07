import logging
import re
import subprocess
from pathlib import Path

import typer

from gsrb.utils.app import get_version
from gsrb.utils.logging import config_logger

logger = logging.getLogger("gsrb.cli.batch_repair")


def batch_repair(
    script_paths: list[Path],
    generate: bool = False,
    device: str = "emulator-5556",
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
            pattern = r"\d\d\.zip" if not generate else r"\d\d\.generate\.zip"
            if re.match(pattern, script.name):
                logger.info(f"repair {script.name}")
                cmd: list[str | Path] = [
                    "repair",
                    script_path,
                    script.name.split(".")[0],
                    "--device",
                    device,
                ]
                if generate:
                    cmd.append("--generate")
                subprocess.run(cmd)


def main() -> None:
    typer.run(batch_repair)
