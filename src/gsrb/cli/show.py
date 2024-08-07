import re
import zipfile
from pathlib import Path
from traceback import format_exc
from typing import Annotated, Optional

import typer


def _show(filename: Path, generate: bool) -> None:
    with zipfile.ZipFile(filename, "r") as zf:
        root = zipfile.Path(zf)
        if generate:
            content = (root / "record_with_assertion.txt").read_text(encoding="utf-8")
        else:
            content = (root / "record.txt").read_text(encoding="utf-8")
    print(content)


def show(
    record_path: Annotated[
        Path, typer.Argument(exists=True, file_okay=False, resolve_path=True)
    ],
    id: Optional[str] = typer.Argument(default=None),
    generate: bool = False,
) -> None:
    records: list[Path] = []
    if id is not None:
        filename = f"{id}.zip" if not generate else f"{id}.generate.zip"
        records.append(record_path / filename)
    else:
        pattern = r"\d\d\.zip" if not generate else r"\d\d\.generate\.zip"
        for filepath in record_path.iterdir():
            if re.match(pattern, filepath.name):
                records.append(filepath)

    for record in records:
        print(record.resolve())
        try:
            _show(record, generate)
        except Exception:
            print(format_exc())


def main() -> None:
    typer.run(show)
