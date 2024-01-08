import time
from pathlib import Path
from multiprocessing import Process

from tele import Telegram
from db import (
    create_profile_if_not_exists,
    create_session
)

profiles = Path(__file__).parent / 'profile_files'
logs = Path(__file__).parent / 'logs'

if not logs.exists():
    logs.mkdir()


#  1. Create Multiple Instances of the Bot -Each bot instance should have its own browser instance, possibly using separate
#  user profiles for each to maintain isolated sessions. It could be achieved with multiprocessing.
def run_profile(auth_storage_filepath: str, acc_id: str) -> None:
    telegram = Telegram(auth_storage_filepath, acc_id)
    telegram.telegram_login_with_proxy()
    print('Program successfully executed')
    while True:
        try:
            time.sleep(1)

        except KeyboardInterrupt:
            break
    try:
        telegram.driver.close()
    except:
        pass


def main() -> None:
    with create_session() as session:

        user_profiles = [
            create_profile_if_not_exists(
                storage_filepath=str(profiles / 'p15_local_storage.json'),
                message='Hello, world!',
                users_list="jemass,arjunk012",
                session=session
            ),
            create_profile_if_not_exists(
                storage_filepath=str(profiles / 'p249_local_storage.json'),
                message='Hello, world!',
                users_list="jemass,arjunk012",
                session=session
            ),
            # create_profile_if_not_exists(
            #     storage_filepath=str(profiles / 'p250_local_storage.json'),
            #     message='Hello, world!',
            #     users_list="jemass",
            #     session=session
            # ),
            # create_profile_if_not_exists(
            #     storage_filepath=str(profiles / 'p251_local_storage.json'),
            #     message='Hello, world!',
            #     users_list="jemass,arjunk012",
            #     session=session
            # ),
        ]

        processes = []

        for profile in user_profiles:
            process = Process(
                target=run_profile,
                args=(profile.storage_filepath, profile.id)
            )
            process.start()
            processes.append(process)

    for process in processes:
        process.join()


if __name__ == '__main__':
    main()
