import datetime
from pathlib import Path

from sqlalchemy import create_engine, DateTime
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

    # 1.For now there are separate report files for every account(logs_1,logs_2...).The problem is that it is not clear whitch report for whitch account is
    # and it is not very pleasant to read(imagine when we have more than 200 acc what it will be to read this reports and to know whitch one for whitch acc is).
    # Also,it should be made in a table in the DB(like account-report message for this account).It is not shown the expiration day,the feedback message when something happens is-
    # "Possibly, telegram is block or timing out for `account#2`".We need to know what exactly happened to know what we should do(i dont believe that account#2 is the second loaded local_storage).
    # Also, it will be good to have 1 additional row in the profile table to show if the account is active(active/blocked).
    log_filename: Mapped[str] = mapped_column(nullable=True)

    # 2.For the moment, every bot acc is using the same proxy and fingerprint.The idea is every acc to use different proxy and fingerprint so it wont be so
    # easily detected as a bot(at least not that soon).Suggestion about this is to be added additional 2 rows in the DB(about proxy and fingerprint where they should be added
    # for every acc as it would be more comfortable adding them).
    user_profile_path: Mapped[str] = mapped_column(nullable=False)
    proxy: Mapped[str] = mapped_column(nullable=False)

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

# 3.There should be table it the DB for the message reports,was the message seen/not send/send etc.(The table should look something like:
# bot acc - user we write to - the message we send - status of the message - counter for the messages sent to this acc).
class Message(Base):

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(nullable=False)
    message: Mapped[str] = mapped_column(nullable=False)
    username: Mapped[str] = mapped_column(nullable=False)
    sent_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    state: Mapped[str] = mapped_column(nullable=False)


engine = create_engine(
    f'sqlite:///{Path(__file__).parent / "service.db"}'  # change to postgresql in prod
)
Base.metadata.create_all(bind=engine)


def create_session() -> Session:
    return Session(engine)


def create_profile_if_not_exists(
        storage_filepath: str,
        message: str,
        users_list: str,
        session: Session,
        user_profile_path: str,
        proxy: str,
        logs_filename: str = None
) -> Profile:
    profile = session.query(Profile).where(
        Profile.storage_filepath == storage_filepath
    ).first()
    if profile is None:
        profile = Profile(
            storage_filepath=storage_filepath,
            message=message,
            users_list=users_list,
            user_profile_path=user_profile_path,
            proxy=proxy,
            log_filename=logs_filename
        )
        session.add(profile)
        session.commit()
    return profile
