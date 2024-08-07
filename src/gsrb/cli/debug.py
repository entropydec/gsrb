import typer
from uiautomator2 import connect

from gsrb.match.layout import Layout
from gsrb.match.predictors import optimize_filter_generator, optimize_key_generator
from gsrb.utils.logging import config_logger


def main() -> None:
    typer.run(debug)


def debug(device: str) -> None:
    config_logger()
    d = connect(device)
    layout = Layout.from_device(d)
    optimize_filter = optimize_filter_generator(layout.non_overlap)
    children = optimize_filter(layout.children)
    optimize_key = optimize_key_generator(children)
    children.sort(key=optimize_key)
    for child in children:
        print(child, optimize_key(child))
    layout.draw(children, with_index=True)
