"""Reports З-1…З-3 in JSON (for the admin UI), CSV and PDF."""

from datetime import date
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Query, Response

from app.api.deps import ADMIN_ONLY, ClockDep, DbSession
from app.api.errors import ERROR_RESPONSES
from app.services.reports.exporters import EXPORTERS
from app.services.reports.generators import GENERATORS, ReportParams
from app.services.reports.proxy import CachingReportProxy

router = APIRouter(prefix="/reports", tags=["Звіти"], responses=ERROR_RESPONSES, dependencies=ADMIN_ONLY)

Format = Annotated[Literal["json", "csv", "pdf"], Query(description="json — для інтерфейсу; csv, pdf — файл")]
Start = Annotated[date | None, Query(description="Початок періоду")]
End = Annotated[date | None, Query(description="Кінець періоду (включно)")]


def _render(code: str, params: ReportParams, export_format: str, db: DbSession, clock: ClockDep) -> Any:
    generator = GENERATORS[code](db, clock)
    report = CachingReportProxy(generator, clock).generate(params)  # GoF Proxy in front of the generator
    exporter = EXPORTERS[export_format]()  # GoF Strategy chosen by the request
    content = exporter.export(report)
    if export_format == "json":
        return content
    return Response(
        content=content,
        media_type=exporter.media_type,
        headers={"Content-Disposition": f'attachment; filename="{exporter.filename(report)}"'},
    )


@router.get("/client-activity", summary="З-1. Клієнти та активність відвідувань (адміністратор)")
def client_activity(
    db: DbSession, clock: ClockDep, start: Start = None, end: End = None, format: Format = "json"
) -> Any:
    return _render("client-activity", ReportParams(start=start, end=end), format, db, clock)


@router.get("/income", summary="З-2. Доходи клубу за місяць або рік (адміністратор)")
def income(
    db: DbSession,
    clock: ClockDep,
    year: Annotated[int | None, Query(ge=2000, le=2100, description="Рік; без місяця — звіт за рік")] = None,
    month: Annotated[int | None, Query(ge=1, le=12, description="Місяць; без параметрів — поточний")] = None,
    format: Format = "json",
) -> Any:
    return _render("income", ReportParams(year=year, month=month), format, db, clock)


@router.get("/load", summary="З-3. Завантаженість тренерів і залів по днях тижня (адміністратор)")
def load(
    db: DbSession, clock: ClockDep, start: Start = None, end: End = None, format: Format = "json"
) -> Any:
    return _render("load", ReportParams(start=start, end=end), format, db, clock)
