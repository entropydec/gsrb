"""定义数据类 Step 以及加载操作序列的相关方法"""
import logging
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple

from gsrb.common.event import Event

logger = logging.getLogger(__name__)


class Ui(NamedTuple):
    """界面

    对当前界面信息的抽象，包括布局信息与截屏信息
    """

    x: str = ""
    p: bytes = bytes()

    def empty(self) -> bool:
        return len(self.x) == 0 and len(self.p) == 0


@dataclass(frozen=True)
class Step:
    """表示操作步骤的数据类

    与 Event 基本相同，额外增加了操作前后的界面信息
    """

    event: Event
    ui_before: Ui = field(default_factory=Ui)
    ui_after: Ui = field(default_factory=Ui)

    def __repr__(self) -> str:
        return repr(self.event)

    def has_ui(self) -> bool:
        return not self.ui_before.empty() and not self.ui_after.empty()


TestCase = list[Step]


def load_testcase(
    path: Path | str, generate: bool = False
) -> tuple[TestCase, str | None]:
    """从文件系统加载操作序列

    可以是 zip 文件，也可以是对应文件解压后的目录。目录中 record.txt 记录了 n 条 Event 数据

    子目录 ui 存储了界面信息，共 2n 个界面，编号 i 的 event 对应的执行前后界面编号分别为 2i 和 2i + 1

    Args:
        path (os.PathLike): 操作序列所在路径

    Returns:
        tuple[TestCase, str | None]: 操作序列与 pretest 脚本
    """
    if not isinstance(path, Path):
        path = Path(path)

    def load_ui(i: int) -> tuple[Ui, Ui]:
        lb = (root / "ui" / f"{i * 2}.xml").read_text(encoding="utf-8")
        sb = (root / "ui" / f"{i * 2}.png").read_bytes()
        la = (root / "ui" / f"{i * 2 + 1}.xml").read_text(encoding="utf-8")
        sa = (root / "ui" / f"{i * 2 + 1}.png").read_bytes()
        return Ui(lb, sb), Ui(la, sa)

    result: TestCase = []
    root: Path | zipfile.Path = path
    zf = None
    if not path.is_dir():
        zf = zipfile.ZipFile(path, "r")
        root = zipfile.Path(zf)
    pretest = None

    # read pretest script if exists
    try:
        pretest = (root / "pretest.py").read_text(encoding="utf-8")
    except Exception:
        pass

    # read event sequence
    if generate:
        events_str = (root / "record_with_assertion.txt").read_text(encoding="utf-8")
    else:
        events_str = (root / "record.txt").read_text(encoding="utf-8")
    events = [Event.from_json(x) for x in events_str.split("\n") if len(x.strip()) != 0]

    i = 0
    for event in events:
        if event.parameter.get("generated", False):
            result.append(Step(event))
        else:
            result.append(Step(event, *load_ui(i)))
            i += 1

    if zf is not None:
        zf.close()

    return result, pretest
