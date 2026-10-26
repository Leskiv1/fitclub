from sqlalchemy.orm import Session

from app.domain.models import ClubSettings


class ClubSettingsRepository:
    """The settings table has a single row created by the initial migration."""

    SETTINGS_ID = 1

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self) -> ClubSettings:
        settings = self.session.get(ClubSettings, self.SETTINGS_ID)
        if settings is None:
            raise LookupError("club_settings row is missing — run `alembic upgrade head`")
        return settings
