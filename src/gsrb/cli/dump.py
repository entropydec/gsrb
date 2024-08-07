from pathlib import Path

import typer
import uiautomator2 as u2


def dump(device: str, name: str) -> None:
    d = u2.connect(device)
    print(d.info)
    Path(f"{name}.xml").write_text(d.dump_hierarchy(pretty=True), encoding="utf-8")
    d.screenshot(filename=f"{name}.png")


def main() -> None:
    typer.run(dump)
