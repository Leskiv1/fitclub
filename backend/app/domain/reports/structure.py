"""Structure of a report as a tree of sections and the builder that assembles it."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal, Protocol

ColumnKind = Literal["text", "int", "number", "money", "percent", "date"]
Value = str | int | float | Decimal | date | None


@dataclass(frozen=True)
class Column:
    key: str
    label: str
    kind: ColumnKind = "text"


class ReportWriter(Protocol):
    """What a section needs from an output format; implemented by the export strategies."""

    def begin_section(self, title: str | None, level: int) -> None: ...
    def end_section(self) -> None: ...
    def summary(self, title: str | None, items: list[tuple[str, Value, ColumnKind]]) -> None: ...
    def table(
        self,
        title: str | None,
        columns: list[Column],
        rows: list[dict[str, Value]],
        totals: dict[str, Value] | None,
    ) -> None: ...


class ReportSection(ABC):
    """GoF: Composite — Component: a part of a report that can write itself to any output format."""

    def __init__(self, title: str | None = None) -> None:
        self.title = title

    @abstractmethod
    def write(self, writer: ReportWriter, level: int = 0) -> None: ...


class SummarySection(ReportSection):
    """GoF: Composite — Leaf: key figures (label → value)."""

    def __init__(self, title: str | None, items: list[tuple[str, Value, ColumnKind]]) -> None:
        super().__init__(title)
        self.items = items

    def write(self, writer: ReportWriter, level: int = 0) -> None:
        writer.summary(self.title, self.items)


class TableSection(ReportSection):
    """GoF: Composite — Leaf: a table with optional totals row."""

    def __init__(
        self,
        title: str | None,
        columns: list[Column],
        rows: list[dict[str, Value]],
        totals: dict[str, Value] | None = None,
    ) -> None:
        super().__init__(title)
        self.columns = columns
        self.rows = rows
        self.totals = totals

    def write(self, writer: ReportWriter, level: int = 0) -> None:
        writer.table(self.title, self.columns, self.rows, self.totals)


class CompositeSection(ReportSection):
    """GoF: Composite — Composite: a section made of other sections, written recursively."""

    def __init__(self, title: str | None = None, children: list[ReportSection] | None = None) -> None:
        super().__init__(title)
        self.children: list[ReportSection] = children or []

    def add(self, section: ReportSection) -> None:
        self.children.append(section)

    def write(self, writer: ReportWriter, level: int = 0) -> None:
        writer.begin_section(self.title, level)
        for child in self.children:
            child.write(writer, level + 1)
        writer.end_section()


@dataclass
class Report:
    """A finished report: metadata plus the root of the section tree."""

    code: str
    title: str
    period_label: str
    generated_at: datetime
    root: CompositeSection
    parameters: dict[str, Any] = field(default_factory=dict)


class ReportBuilder:
    """GoF: Builder — assembles a Report step by step; groups may be nested.

    builder.summary(...).group("Тренери").table(...).table(...).end_group().build()
    """

    def __init__(self, code: str, title: str, generated_at: datetime) -> None:
        self._code = code
        self._title = title
        self._generated_at = generated_at
        self._period_label = ""
        self._parameters: dict[str, Any] = {}
        self._stack: list[CompositeSection] = [CompositeSection(title)]

    def period(self, label: str, **parameters: Any) -> ReportBuilder:
        self._period_label = label
        self._parameters = parameters
        return self

    def summary(self, title: str | None, items: list[tuple[str, Value, ColumnKind]]) -> ReportBuilder:
        self._stack[-1].add(SummarySection(title, items))
        return self

    def table(
        self,
        title: str | None,
        columns: list[Column],
        rows: list[dict[str, Value]],
        totals: dict[str, Value] | None = None,
    ) -> ReportBuilder:
        self._stack[-1].add(TableSection(title, columns, rows, totals))
        return self

    def group(self, title: str) -> ReportBuilder:
        section = CompositeSection(title)
        self._stack[-1].add(section)
        self._stack.append(section)
        return self

    def end_group(self) -> ReportBuilder:
        if len(self._stack) == 1:
            raise RuntimeError("end_group() without a matching group()")
        self._stack.pop()
        return self

    def build(self) -> Report:
        if len(self._stack) != 1:
            raise RuntimeError("a group() was not closed")
        return Report(
            code=self._code,
            title=self._title,
            period_label=self._period_label,
            generated_at=self._generated_at,
            root=self._stack[0],
            parameters=self._parameters,
        )
