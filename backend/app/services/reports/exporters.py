"""Export of a report to JSON (for the UI), CSV and PDF."""

import csv
import io
from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from fpdf import FPDF
from fpdf.fonts import FontFace

from app.domain.reports.structure import Column, ColumnKind, Report, Value

FONTS = Path(__file__).resolve().parents[2] / "assets" / "fonts"


class ReportExporter(ABC):
    """GoF: Strategy — Strategy: turns a report into a file of some format.

    Exporters are also the writers that the Composite sections write themselves to.
    """

    media_type: str
    extension: str

    @abstractmethod
    def export(self, report: Report) -> bytes | dict[str, Any]: ...

    def filename(self, report: Report) -> str:
        start, end = report.parameters["start"], report.parameters["end"]
        return f"{report.code}_{start:%Y-%m-%d}_{end:%Y-%m-%d}.{self.extension}"


class JsonExporter(ReportExporter):
    """GoF: Strategy — ConcreteStrategy: nested sections for the admin UI (tables and charts)."""

    media_type = "application/json"
    extension = "json"

    def export(self, report: Report) -> dict[str, Any]:
        self._stack: list[list[dict[str, Any]]] = [[]]
        report.root.write(self)
        return {
            "code": report.code,
            "title": report.title,
            "period": report.period_label,
            "parameters": {key: str(value) for key, value in report.parameters.items()},
            "generated_at": report.generated_at.isoformat(),
            "sections": self._stack[0][0]["sections"],
        }

    def begin_section(self, title: str | None, level: int) -> None:
        section = {"type": "group", "title": title, "sections": []}
        self._stack[-1].append(section)
        self._stack.append(section["sections"])

    def end_section(self) -> None:
        self._stack.pop()

    def summary(self, title: str | None, items: list[tuple[str, Value, ColumnKind]]) -> None:
        self._stack[-1].append(
            {
                "type": "summary",
                "title": title,
                "items": [{"label": label, "value": value, "kind": kind} for label, value, kind in items],
            }
        )

    def table(self, title, columns, rows, totals) -> None:
        self._stack[-1].append(
            {
                "type": "table",
                "title": title,
                "columns": [{"key": c.key, "label": c.label, "kind": c.kind} for c in columns],
                "rows": rows,
                "totals": totals,
            }
        )


def _plain(value: Value, kind: ColumnKind) -> str:
    """Text for CSV/PDF in Ukrainian conventions: 1 234,50 · 27.10.2026."""
    if value is None:
        return ""
    if isinstance(value, date):
        return f"{value:%d.%m.%Y}"
    if kind == "money" or isinstance(value, Decimal):
        return f"{Decimal(value):,.2f}".replace(",", " ").replace(".", ",")
    if kind in ("percent", "number") and isinstance(value, float):
        return f"{value:.1f}".replace(".", ",")
    return str(value)


class CsvExporter(ReportExporter):
    """GoF: Strategy — ConcreteStrategy: CSV that the Ukrainian Excel opens correctly (UTF-8 BOM, ';')."""

    media_type = "text/csv; charset=utf-8"
    extension = "csv"

    def export(self, report: Report) -> bytes:
        self._buffer = io.StringIO()
        self._csv = csv.writer(self._buffer, delimiter=";", lineterminator="\r\n")
        self._csv.writerow([report.title])
        self._csv.writerow(["Період", report.period_label])
        report.root.write(self)
        return ("﻿" + self._buffer.getvalue()).encode("utf-8")

    def begin_section(self, title: str | None, level: int) -> None:
        if level > 0 and title:
            self._csv.writerows([[], [title]])

    def end_section(self) -> None:
        return None

    def summary(self, title, items) -> None:
        self._csv.writerows([[], [title or ""]])
        self._csv.writerows([[label, _plain(value, kind)] for label, value, kind in items])

    def table(self, title: str | None, columns: list[Column], rows, totals) -> None:
        self._csv.writerows([[], [title or ""], [c.label for c in columns]])
        for row in [*rows, *([totals] if totals else [])]:
            self._csv.writerow([_plain(row.get(c.key), c.kind) for c in columns])


class PdfExporter(ReportExporter):
    """GoF: Strategy — ConcreteStrategy: a printable PDF with Cyrillic (embedded DejaVu Sans)."""

    media_type = "application/pdf"
    extension = "pdf"

    def export(self, report: Report) -> bytes:
        pdf = FPDF(orientation="L", format="A4")
        pdf.add_font("DejaVu", "", FONTS / "DejaVuSans.ttf")
        pdf.add_font("DejaVu", "B", FONTS / "DejaVuSans-Bold.ttf")
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.add_page()
        pdf.set_font("DejaVu", "B", 16)
        pdf.cell(0, 10, report.title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("DejaVu", "", 10)
        pdf.cell(
            0, 6, f"Період: {report.period_label} · сформовано {report.generated_at:%d.%m.%Y %H:%M}",
            new_x="LMARGIN", new_y="NEXT",
        )  # fmt: skip
        self._pdf = pdf
        report.root.write(self)
        return bytes(pdf.output())

    def begin_section(self, title: str | None, level: int) -> None:
        if level > 0 and title:
            self._heading(title, 13)

    def end_section(self) -> None:
        return None

    def summary(self, title, items) -> None:
        self._heading(title, 12)
        self._pdf.set_font("DejaVu", "", 10)
        with self._pdf.table(
            col_widths=(3, 1), first_row_as_headings=False, width=150, align="LEFT"
        ) as table:
            for label, value, kind in items:
                table.row([label, _plain(value, kind)])

    def table(self, title, columns: list[Column], rows, totals) -> None:
        self._heading(title, 12)
        self._pdf.set_font("DejaVu", "", 7 if len(columns) > 8 else 9)
        with self._pdf.table(headings_style=self._bold(), text_align="LEFT") as table:
            table.row([c.label for c in columns])
            for row in rows:
                table.row([_plain(row.get(c.key), c.kind) for c in columns])
            if totals:
                table.row([_plain(totals.get(c.key), c.kind) for c in columns], style=self._bold())

    def _heading(self, title: str | None, size: int) -> None:
        if title:
            self._pdf.ln(3)
            self._pdf.set_font("DejaVu", "B", size)
            self._pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")

    @staticmethod
    def _bold() -> FontFace:
        return FontFace(family="DejaVu", emphasis="BOLD")


EXPORTERS: dict[str, type[ReportExporter]] = {"json": JsonExporter, "csv": CsvExporter, "pdf": PdfExporter}
