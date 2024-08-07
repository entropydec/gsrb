import logging

import typer
import uiautomator2 as u2

from gsrb.match.draw import draw_match
from gsrb.match.layout import Layout
from gsrb.utils.logging import config_logger

logger = logging.getLogger(__name__)


def diff_layout(devices: tuple[str, str] = ("emulator-5554", "emulator-5556")) -> None:
    config_logger()
    d1 = u2.connect(devices[0])
    d2 = u2.connect(devices[1])
    old = Layout.from_device(d1)
    new = Layout.from_device(d2)
    # from gsrb.match.match import MatchInfo, draw_matches
    # info = MatchInfo(old, new)
    # draw_matches(info.old.png, info.new.png, info.matched_points)
    image, diff_dicts = draw_match(old, new)
    for diff_dict in diff_dicts:
        logger.info(diff_dict)
    image.show()


def main() -> None:
    typer.run(diff_layout)
