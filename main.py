import time
from pathlib import Path
from multiprocessing import Process

from tele import Telegram
from db import (
    create_profile_if_not_exists,
    create_session,
    Profile
)

profiles = Path(__file__).parent / 'profile_files'
logs = Path(__file__).parent / 'logs'
user_data_dirs = Path(__file__).parent / 'user_data_dirs'


if not logs.exists():
    logs.mkdir()


# 1. Create Multiple Instances of the Bot -Each bot instance should have its own browser instance, possibly using
# separate user profiles for each to maintain isolated sessions. It could be achieved with multiprocessing.
# ______________________________________________________________________________________________________________________
# 1.For now there are separate report files for every account(logs_1,logs_2...).The problem is that it is not clear whitch report for whitch account is
# and it is not very pleasant to read(imagine when we have more than 200 acc what it will be to read this reports and to know whitch one for whitch acc is).
# Also,it should be made in a table in the DB(like account-report message for this account).It is not shown the expiration day,the feedback message when something happens is-
# "Possibly, telegram is block or timing out for `account#2`".We need to know what exactly happened to know what we should do(i dont believe that account#2 is the second loaded local_storage).
# Also, it will be good to have 1 additional row in the profile table to show if the account is active(active/blocked).
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
    telegram.write_to_users()
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
        create_profile_if_not_exists(
            storage_filepath=str(profiles / 'p15_local_storage.json'),
            message='Hello, world!',
            users_list="jemass,arjunk012",
            session=session,
            user_profile_path=str(user_data_dirs / 'p15'),
            proxy='gate.smartproxy.com:7000:user-spbk2q6zpf-country-bg:8cmj5iVzxPy2jgD2zX',
            logs_filename='p15.log'
        )
        create_profile_if_not_exists(
            storage_filepath=str(profiles / 'p249_local_storage.json'),
            message='Hello, world!',
            users_list="mrsdfff",
            session=session,
            user_profile_path=str(user_data_dirs / 'p249'),
            proxy='gate.smartproxy.com:7000:user-spbk2q6zpf-country-bg:8cmj5iVzxPy2jgD2zX',
            logs_filename='p249.log'
        )
        # create_profile_if_not_exists(
        #     storage_filepath=str(profiles / 'p250_local_storage.json'),
        #     message='Hello, world!',
        #     users_list="jemass",
        #     session=session
        # ),
        create_profile_if_not_exists(
            storage_filepath=str(profiles / 'p251_local_storage.json'),
            message='Hello, world!',
            users_list="akel7leads",
            session=session,
            user_profile_path=str(user_data_dirs / 'p251'),
            proxy='gate.smartproxy.com:7000:user-spbk2q6zpf-country-bg:8cmj5iVzxPy2jgD2zX',
            logs_filename='p251.log'
        )

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
