"""Club settings (ЗВ-7): opening hours, reminder period, time of the daily check."""

from fastapi import APIRouter

from app.api.deps import ADMIN_ONLY, DbSession
from app.api.errors import ERROR_RESPONSES
from app.schemas.notifications import ClubSettingsRead, ClubSettingsUpdate
from app.services.club_settings import ClubSettingsService

router = APIRouter(prefix="/settings", tags=["Налаштування клубу"], responses=ERROR_RESPONSES)


@router.get("", summary="Налаштування клубу (публічно: години роботи для сайту)")
def get_settings(db: DbSession) -> ClubSettingsRead:
    return ClubSettingsRead.from_model(ClubSettingsService(db).get())


@router.patch("", summary="Змінити налаштування (адміністратор)", dependencies=ADMIN_ONLY)
def update_settings(data: ClubSettingsUpdate, db: DbSession) -> ClubSettingsRead:
    return ClubSettingsRead.from_model(ClubSettingsService(db).update(data.model_dump(exclude_unset=True)))
