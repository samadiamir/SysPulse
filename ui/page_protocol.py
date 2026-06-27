"""
ui/page_protocol.py

Formal interface for anything that receives live data ticks.
Using typing.Protocol gives us structural subtyping — pages don't
need to inherit from anything; they just need to implement the method.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from core.snapshot import Snapshot


@runtime_checkable
class PageSubscriber(Protocol):
    """Any widget that can receive a data snapshot."""

    def update_data(self, snapshot: Snapshot) -> None: ...
