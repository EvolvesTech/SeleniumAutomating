import time
from multiprocessing import Process
from pathlib import Path

from tele import Telegram
from db import (
    create_session,
    Profile
)

profiles = Path(__file__).parent / 'profile_files'
logs = Path(__file__).parent / 'logs'
user_data_dirs = Path(__file__).parent / 'user_data_dirs'


if not logs.exists():
    logs.mkdir()


def run_profile(
        auth_storage_filepath: str,
        acc_id: str,
        proxy: str,
        user_data_dir: str,
        logs_filename: str
) -> None:
    telegram = Telegram(
        auth_local_storage_path=auth_storage_filepath,
        account_id=acc_id,
        user_profiles_path=user_data_dir,
        proxy=proxy,
        logs_filename=logs_filename
    )
    telegram.check_messages_state()
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

        user_profiles = session.query(Profile).all()

        processes = []

        for profile in user_profiles:

            if profile.id == 1:
                continue

            process = Process(
                target=run_profile,
                args=(
                    profile.storage_filepath,
                    profile.id,
                    profile.proxy,
                    profile.user_profile_path,
                    profile.log_filename
                )
            )
            process.start()
            processes.append(process)

    for process in processes:
        process.join()


if __name__ == '__main__':
    main()