import re
from pathlib import Path
from typing import Annotated

import pandas as pd
import typer


def count(
    directory: Annotated[
        Path, typer.Argument(exists=True, file_okay=False, resolve_path=True)
    ] = Path.cwd()
) -> None:
    df = pd.read_excel("data/apk.xlsx", sheet_name="final")
    for i, row in df.iterrows():
        if not isinstance(package := row["package"], str):
            break

        script_name = f"{row['testcase_id']}.repaired.generate.py"
        script_path = directory / package / script_name
        repair_time = ""
        explore_time = ""
        if script_path.exists():
            lines = script_path.read_text("utf-8").split("\n")
            if (match := re.match("# repair time: (.*)s", lines[0])) is not None:
                repair_time = match.group(1)
            if (match := re.match("# explore time: (.*)", lines[1])) is not None:
                explore_time = match.group(1)
        print(f"{package},{script_name},{repair_time},{explore_time}")


def main() -> None:
    typer.run(count)
