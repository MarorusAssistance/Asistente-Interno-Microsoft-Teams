from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from internal_assistant.schemas import ChatResponse

from evaluation.types import ExpandedEvaluationTurn


class BaseJudge(ABC):
    @abstractmethod
    def judge(self, turn: ExpandedEvaluationTurn, response: ChatResponse, meta: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

