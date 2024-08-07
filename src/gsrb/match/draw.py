import io
import logging

from PIL import Image
from PIL.ImageDraw import Draw

from gsrb.match.layout import Layout
from gsrb.match.match import match_layout
from gsrb.match.predictors import is_diff
from gsrb.utils.element import coordinates

logger = logging.getLogger(__name__)


def get_canvas(old: bytes, new: bytes) -> tuple[Image.Image, int]:
    with io.BytesIO(old) as of, io.BytesIO(new) as nf, Image.open(of) as oi, Image.open(
        nf
    ) as ni:
        width = oi.width + ni.width
        height = max(oi.height, ni.height)
        image = Image.new("RGB", (width, height))
        image.paste(oi, (0, 0))
        image.paste(ni, (oi.width, 0))
        return image, oi.width


def draw_match(
    old: Layout, new: Layout
) -> tuple[Image.Image, list[dict[str, tuple[str, str]]]]:
    canvas, offset = get_canvas(old.png, new.png)
    draw = Draw(canvas)
    diff_dicts: list[dict[str, tuple[str, str]]] = []
    result = match_layout(old, new)

    # draw matched
    for k, v in result.matched.items():
        diff_dict: dict[str, tuple[str, str]] = dict()
        if is_diff(k, v, diff_dict=diff_dict):
            diff_dicts.append(diff_dict)

            x0, y0, x1, y1 = coordinates(k)
            center0 = ((x0 + x1) / 2, (y0 + y1) / 2)
            x2, y2, x3, y3 = coordinates(v)
            center1 = ((x2 + x3) / 2 + offset, (y2 + y3) / 2)

            draw.rectangle((x0, y0, x1, y1), width=5, outline="#00FF00")
            draw.rectangle(
                (x2 + offset, y2, x3 + offset, y3),
                width=5,
                outline="#00FF00",
            )
            draw.line([center0, center1], width=3, fill="#00FF00")

    # draw possible
    for k, v_list in result.possible.items():
        x0, y0, x1, y1 = coordinates(k)
        center0 = ((x0 + x1) / 2, (y0 + y1) / 2)
        draw.rectangle((x0, y0, x1, y1), width=5, outline="#0000FF")
        for v in v_list:
            x2, y2, x3, y3 = coordinates(v)
            center1 = ((x2 + x3) / 2 + offset, (y2 + y3) / 2)
            draw.rectangle(
                (x2 + offset, y2, x3 + offset, y3),
                width=5,
                outline="#0000FF",
            )
            draw.line([center0, center1], width=3, fill="#0000FF")

    # draw not match
    for n in result.old_not_matched:
        draw.rectangle(coordinates(n), width=5, outline="#FF0000")
    for n in result.new_not_matched:
        x0, y0, x1, y1 = coordinates(n)
        draw.rectangle((x0 + offset, y0, x1 + offset, y1), width=5, outline="#FF0000")

    return canvas, diff_dicts
