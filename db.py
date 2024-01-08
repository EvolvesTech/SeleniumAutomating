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

#  3. Customizable Initial Message External Message Configuration: Store the initial messages in a
#  database or a configuration file. This allows you to change the message without modifying the bot's source code.
#
#  Dynamic Message Retrieval: Update the bot to read the current message from the external source right before
#  sending a message, ensuring it always uses the latest version.
#
#  4. Editable Usernames List External Usernames Storage: Use a database or a file to store the list of usernames.
#  Ensure the storage method allows easy updating of the list.
#  Dynamic Usernames Retrieval: Create a function within the bot that fetches the latest list of usernames
#  from the external source before starting its operations.


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


#  7. Messaging Frequency Limits Rate Limiting Algorithm: Design an algorithm to enforce limits on the
#  number of messages sent. This might involve tracking the time of each sent message and checking against daily,
#  weekly, and monthly limits.
#
#  Limit Enforcement: Prior to sending a message, the bot should verify that it hasn't exceeded its messaging quota
#   and should stop until the limit resets.

class ProfileLimit(Base):

    __tablename__ = "profile_limits"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(nullable=False)
    day_counter: Mapped[int] = mapped_column(default=0)
    week_counter: Mapped[int] = mapped_column(default=0)
    month_counter: Mapped[int] = mapped_column(default=0)
    day_limit: Mapped[int] = mapped_column(default=100)
    week_limit: Mapped[int] = mapped_column(default=700)
    month_limit: Mapped[int] = mapped_column(default=3000)
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
