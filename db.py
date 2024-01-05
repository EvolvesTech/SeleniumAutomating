import datetime
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    Session
)
from sqlalchemy.ext.hybrid import hybrid_property


class Base(DeclarativeBase):
    pass


class Profile(Base):

    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    storage_filepath: Mapped[str] = mapped_column(nullable=False)
    message: Mapped[str] = mapped_column(nullable=False)
    users_list: Mapped[str] = mapped_column(nullable=False)

    @hybrid_property
    def users(self):
        # noinspection PyUnresolvedReferences
        return self.users_list.split(',')


class ProfileLimit(Base):

    __tablename__ = "profile_limits"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(nullable=False)
    day_limit: Mapped[int] = mapped_column(default=0)
    week_limit: Mapped[int] = mapped_column(default=0)
    month_limit: Mapped[int] = mapped_column(default=0)
    last_message_date: Mapped[datetime.datetime] = mapped_column(nullable=False)


engine = create_engine(
    f'sqlite:///{Path(__file__).parent / "service.db"}'  # change to postgresql in prod
)
Base.metadata.create_all(bind=engine)


def create_session() -> Session:
    return Session(engine)


def create_profile_if_not_exists(
    storage_filepath: str, message: str, users_list: str, session: Session
) -> Profile:
    profile = session.query(Profile).where(
        Profile.storage_filepath == storage_filepath
    ).first()
    if profile is None:
        profile = Profile(
            storage_filepath=storage_filepath,
            message=message,
            users_list=users_list,
        )
        session.add(profile)
        session.commit()
    return profile
