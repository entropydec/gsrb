import json
import logging
import time
from datetime import datetime
from importlib.resources import files
from traceback import format_exc
from typing import Literal, TypedDict

import openai

import gsrb.record
from gsrb.common.action import Action
from gsrb.common.criterion import Criterion
from gsrb.common.event import Event
from gsrb.common.locator import Locator
from gsrb.common.step import Step
from gsrb.match.layout import Layout

logger = logging.getLogger(__name__)

prompt = files(gsrb.record).joinpath("prompt.md").read_text(encoding="utf-8")
openai.api_key = files(gsrb.record).joinpath("key").read_text(encoding="utf-8")
openai.proxy = "http://127.0.0.1:7890"  # type: ignore


class Message(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str


Candidate = dict[str, str]


last_request = datetime(1970, 1, 1)


def ask(layout: Layout) -> list[Candidate]:
    global last_request
    # prepare input
    digest = layout.digest
    chat = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": digest},
    ]
    logger.debug(f"layout digest: {digest}")

    # check & update last request time
    now = datetime.now()
    if (interval := (now - last_request).total_seconds()) < 30:
        time.sleep(30 - interval)
    last_request = datetime.now()

    # ask chatgpt
    try:
        response: object = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=chat,
        )  # noqa
    except Exception:
        logger.error(f"openai exception {format_exc()}")
        return []

    # extract answer
    logger.debug(f"raw response: {str(response)}")
    answer: str = response["choices"][0]["message"]["content"]  # type: ignore
    assert isinstance(answer, str)
    logger.debug(f"chatgpt answer: {answer}")

    # deserialize
    answer = answer[answer.find("{") : answer.rfind("}") + 1]
    nodes: list[str] = answer.split("\n")
    try:
        candidates: list[Candidate] = [json.loads(node) for node in nodes]
    except json.JSONDecodeError:
        logger.error(f"deserialize failed {format_exc()}")
        return []

    return candidates


def get_target_indices(steps: list[Step]) -> set[int]:
    target_indices = set()
    length = len(steps)
    if length >= 2:
        target_indices.add((length - 1) // 2)
    target_indices.add(length - 1)

    return target_indices


def retry_ask(layout: Layout, retry_times: int = 3) -> list[Candidate]:
    i = 0
    candidates = ask(layout)
    while i < retry_times and len(candidates) == 0:
        i += 1
        logger.info("retry")
        candidates = ask(layout)
    logger.debug(f"candidates: {candidates}")
    return candidates


def select_candidate(candidates: list[Candidate]) -> Candidate | None:
    for attr in "tdr":
        if (n := next(filter(lambda x: x[attr] != "", candidates), None)) is not None:
            logger.debug(f"selected candidate: {n}")
            return n
    return None


def to_assertion(candidate: Candidate | None) -> Event | None:
    if candidate is None:
        return None
    for attr, c in (("t", Criterion.TEXT), ("d", Criterion.DESC), ("r", Criterion.ID)):
        if candidate[attr] != "":
            result = Event(
                Action.EXIST, Locator({c: candidate[attr]}), {"generated": True}
            )
            logger.debug(f"generated assertion: {result}")
            return result
    return None
