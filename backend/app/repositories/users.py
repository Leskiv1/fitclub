from sqlalchemy import func, select

from app.domain.models import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def get_by_email(self, email: str) -> User | None:
        query = select(User).where(func.lower(User.email) == email.lower())
        return self.session.scalar(query)
