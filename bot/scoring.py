"""Подсчёт баллов на стороне бота.

Ответы приходят из Mini App, но клиенту доверять нельзя: бот сам валидирует
ответы и пересчитывает баллы по тому же tests.json, что использует Mini App.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

TESTS_PATH = Path(__file__).resolve().parent.parent / "webapp" / "tests.json"

with TESTS_PATH.open(encoding="utf-8") as f:
    CONFIG = json.load(f)

TESTS = {t["id"]: t for t in CONFIG["tests"]}


class InvalidPayload(ValueError):
    pass


@dataclass
class SubscaleResult:
    id: str
    title: str
    description: str
    total: int
    level: int
    label: str
    advice: str


@dataclass
class TestResult:
    test_id: str
    title: str
    name: str
    total: int
    max: int
    unit: str
    level: int
    label: str
    advice: str
    crisis: bool
    in_summary: bool = True
    subscales: list[SubscaleResult] = field(default_factory=list)


def _item_values(test: dict, item: dict) -> list[int]:
    return [o["value"] for o in item.get("options", test["options"])]


def _sum(test: dict, answers: list[int], indexes) -> tuple[int, dict]:
    raw = 0
    for i in indexes:
        item, a = test["items"][i], answers[i]
        values = _item_values(test, item)
        raw += max(values) + min(values) - a if item.get("reverse") else a
    s = test["scoring"]
    total = raw * s.get("multiplier", 1)
    band = next(b for b in s["bands"] if total <= b["max"])
    return total, band


def score_test(test: dict, answers: list[int]) -> TestResult:
    items = test["items"]
    if (
        not isinstance(answers, list)
        or len(answers) != len(items)
        or any(a not in _item_values(test, item) for item, a in zip(items, answers))
    ):
        raise InvalidPayload(f"bad answers for {test['id']}")

    s = test["scoring"]
    crisis = any(item.get("crisis") and a > 0 for item, a in zip(items, answers))
    common = dict(test_id=test["id"], title=test["title"], name=test["name"], max=s["max"],
                  unit=s.get("unit", ""), crisis=crisis, in_summary=not test.get("excludeFromSummary"))

    if "subscales" in s:
        subs = []
        for sub in s["subscales"]:
            total, band = _sum(test, answers, sub["items"])
            subs.append(SubscaleResult(sub["id"], sub["title"], sub["description"], total,
                                       band["level"], band["label"], band["advice"]))
        subs.sort(key=lambda x: x.total, reverse=True)
        top = subs[0]
        return TestResult(**common, total=top.total, level=top.level, label=top.label,
                          advice=top.advice, subscales=subs)

    total, band = _sum(test, answers, range(len(items)))
    return TestResult(**common, total=total, level=band["level"], label=band["label"], advice=band["advice"])


def score_payload(raw_json: str) -> list[TestResult]:
    try:
        data = json.loads(raw_json)
        answers = data["answers"]
        assert isinstance(answers, dict) and answers
    except Exception as e:
        raise InvalidPayload("malformed payload") from e

    if not set(answers) <= set(TESTS):
        raise InvalidPayload("unknown test ids")
    # порядок как в tests.json
    return [score_test(test, answers[tid]) for tid, test in TESTS.items() if tid in answers]
