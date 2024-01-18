import datetime
import functools
import os
import pathlib
import sys
import time
import random
import traceback
import typing
import zipfile
from pathlib import Path
import logging

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from seleniumbase.fixtures import page_actions
from seleniumbase.fixtures import page_utils
from seleniumbase.common.exceptions import (
    NoSuchElementException,
    ElementNotVisibleException,
    TimeoutException
)

from db import (
    create_session,
    ProfileLimit,
    Profile,
    Message,
    create_or_update_report
)


_T = typing.TypeVar('_T')
AnyFunction = typing.Callable[..., _T]


def catch_timed_out(function: AnyFunction) -> AnyFunction:
    """
    Decorator to catch timing out, which can be caused by
    telegram blocking the account or some requests
    """

    @functools.wraps(function)
    def wrapper(self, *args, **kwargs) -> _T:
        try:
            return function(self, *args, **kwargs)
        except (TimeoutException, NoSuchElementException):
            message = f'Possibly, telegram is block or timing out for `account#{self.account_id}`'
            self.logger.error(message)
            create_or_update_report(profile_id=self.account_id, message=message)
            sys.exit(0)
    return wrapper


# Spam and Ban Detection: Implement logic to recognize patterns indicating
#  that a bot might be blocked or banned (e.g., repeated failures to send messages, being redirected to unexpected pages,
#   or receiving specific warning messages, no such username, similar names, spam blocked, logged out/ banned).
#   After we run the script we manually check how the script runs and there might be other additional errors that need
#   to be added.
def catch_logged_out(function: AnyFunction) -> AnyFunction:
    @functools.wraps(function)
    def wrapper(self, *args, **kwargs) -> _T:
        try:
            return function(self, *args, **kwargs)

        except SystemExit:
            pass

        except:
            message = f'Can\'t do actions in `account#{self.account_id}`. Possibly session expired.'
            self.logger.error(message)
            self.logger.error(traceback.format_exc())
            create_or_update_report(profile_id=self.account_id, message=message)
            sys.exit(0)
    return wrapper


class LimitExceeded(Exception):
    pass


def catch_limit_exceeded(function: AnyFunction) -> AnyFunction:
    @functools.wraps(function)
    def wrapper(self, *args, **kwargs) -> _T:
        try:
            return function(self, *args, **kwargs)
        except LimitExceeded:
            message = f'Limit exceeded for `account#{self.account_id}`'
            self.logger.error(message)
            create_or_update_report(profile_id=self.account_id, message=message)
            sys.exit(0)
    return wrapper


class Telegram:

    def __init__(
            self,
            auth_local_storage_path: str,
            account_id: str,
            user_profiles_path: str,
            proxy: str,
            logs_filename: str = None,
            max_day_limit: int = 100,
            max_week_limit: int = 700,
            max_month_limit: int = 3000,
    ):
        #  6. Reporting System Logging Mechanism: Develop a robust logging system that captures key activities and statuses.
        #  This might include information like login attempts, messages sent, errors encountered, etc.
        #
        #  Report Generation: Set up a routine to compile these logs into comprehensive reports. You might want to
        #  automate this process to run at regular intervals (e.g., daily or weekly).
        self.logger = logging.getLogger(f"TelegramAccount#{account_id}")
        self.logger.setLevel(logging.DEBUG)

        if logs_filename is None:
            logs_file = Path(__file__).parent / Path('logs') / f"logs_{account_id}.log"
        else:
            logs_file = Path(__file__).parent / Path('logs') / logs_filename

        handler = logging.FileHandler(logs_file)
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(handler)
        self.proxy = proxy
        self.user_profiles_path = pathlib.Path(__file__).parent / Path(user_profiles_path)
        self.max_day_limit = max_day_limit
        self.max_week_limit = max_week_limit
        self.max_month_limit = max_month_limit
        self.account_id = account_id
        self.local_storage_file_path = auth_local_storage_path
        self.driver = self.create_chromedriver(
            USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/88.0.4324.150 Safari/537.36"
        )
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/88.0.4324.150 Safari/537.36"
        })
        self.users_list = []
        self.message = ""
        self.add_random_behavior()

    def add_random_behavior(self) -> None:
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.execute_script("window.navigator.chrome = {runtime: {}}")
        self.driver.execute_script("window.navigator.plugins = [1, 2, 3, 4, 5]")
        self.driver.execute_script("window.navigator.languages = ['en-US', 'en']")

    # Method to introduce random delays in actions to simulate human behavior
    def random_delay(self, min_seconds=2, max_seconds=5):
        time.sleep(random.uniform(min_seconds, max_seconds))

    # Method to move the mouse to an element in a human-like manner
    def human_like_mouse_movement(self, element):
        action = ActionChains(self.driver)
        action.move_to_element(element).perform()
        self.random_delay()

    def save_local_storage(self, path):
        self.logger.info('Saving local storage')
        local_storage = self.driver.execute_script("return JSON.stringify(localStorage);")
        with open(path, 'w', encoding='utf-8') as file:
            file.write(local_storage)
        self.logger.info('Local storage saved successfully')

    def load_local_storage(self, path):
        self.logger.info('Loading local storage')
        with open(path, 'r', encoding='utf-8') as file:
            local_storage = file.read()
        self.driver.execute_script(
            "localStorage.clear(); var data = JSON.parse(arguments[0]); for (var key in data) localStorage.setItem("
            "key, data[key]);",
            local_storage)
        self.logger.info('Local storage loaded successfully')

    def _wait_for_element_visible(
            self,
            selector: str,
            by: str = 'css selector',
            timeout: int = page_actions.settings.LARGE_TIMEOUT,
            extract_from=None
    ) -> WebElement:
        self.logger.info(f'Waiting for element {repr(selector)} to be visible')
        original = selector
        selector, by = page_utils.recalculate_selector(selector, by)
        return page_actions.wait_for_element_visible(
            driver=self.driver if extract_from is None else extract_from,
            selector=selector,
            by=by,
            original_selector=original,
            timeout=timeout
        )
    #  2. Test Outcomes for Various Scenarios Username Validation: Enhance the search functionality to interpret search
    #  results accurately. This involves analyzing the DOM elements to check if the username is found, absent, or if there
    #  are suggestions for similar usernames.
    @catch_timed_out
    def search_for_contact(self, contact_name):

        self.logger.info(f'Searching for contact {repr(contact_name)}')

        self.update_bot_data()

        try:
            search_input = self._wait_for_element_visible("#telegram-search-input")
        except:
            search_input = self._wait_for_element_visible('.input-field-input.input-search-input')

        self.human_like_mouse_movement(search_input)
        search_input.click()
        search_input.clear()
        contact_name = "@" + contact_name
        for char in contact_name:
            search_input.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))

        self.random_delay(4, 5)

    #  7. Messaging Frequency Limits Rate Limiting Algorithm: Design an algorithm to enforce limits on the
    #  number of messages sent. This might involve tracking the time of each sent message and checking against daily,
    #  weekly, and monthly limits.
    #
    #  Limit Enforcement: Prior to sending a message, the bot should verify that it hasn't exceeded its messaging quota
    #   and should stop until the limit resets.
    def limit_check(self) -> None:

        with create_session() as session:

            profile_limit = session.query(ProfileLimit).where(
                ProfileLimit.profile_id == self.account_id
            ).first()

            if profile_limit is None:
                profile_limit = ProfileLimit(
                    profile_id=self.account_id,
                    day_counter=0,
                    week_counter=0,
                    month_counter=0,
                    day_limit=self.max_day_limit,
                    week_limit=self.max_week_limit,
                    month_limit=self.max_month_limit,
                    last_message_date=datetime.datetime.now()
                )
                session.add(profile_limit)
                session.commit()

            if profile_limit.day_counter >= profile_limit.day_limit:
                self.logger.error(f'Day limit exceeded for `account#{self.account_id}`')
                raise LimitExceeded

            if profile_limit.week_counter >= profile_limit.week_limit:
                self.logger.error(f'Week limit exceeded for `account#{self.account_id}`')
                raise LimitExceeded

            if profile_limit.month_counter >= profile_limit.month_limit:
                self.logger.error(f'Month limit exceeded for `account#{self.account_id}`')
                raise LimitExceeded

            profile_limit.last_message_date = datetime.datetime.now()
            profile_limit.day_counter += 1
            profile_limit.week_counter += 1
            profile_limit.month_counter += 1
            session.commit()

    def update_bot_data(self) -> None:
        self.logger.info('Updating bot data')

        with create_session() as session:
            profile = session.query(Profile).where(
                Profile.id == self.account_id
            ).first()
            if profile is None:
                self.logger.error(f'Profile with id {self.account_id} not found')
                sys.exit(0)

            self.users_list = profile.users
            self.message = profile.message

        self.logger.info('Bot data updated successfully')

    @staticmethod
    def _best_coincidence(expected: str, first: WebElement, second: WebElement) -> WebElement:
        try:
            first_text = first.text.strip().replace('@', '')
            first_letters = set(expected) & set(first_text)
        except:
            return second

        try:
            second_text = second.text.strip().replace('@', '')
            second_letters = set(expected) & set(second_text)
        except:
            return first

        if expected.strip() == first_text:
            return first

        if expected.strip() == second_text:
            return second

        return second if second_letters > first_letters else first

    @catch_timed_out
    def click_contact(self, contact_name):
        self.logger.info(f'Trying to click contact {repr(contact_name)}')

        try:
            # Click "Show more" button if exists
            self._wait_for_element_visible('.section-heading [href="#"]', timeout=7).click()
        except:
            pass

        try:
            contact_selector = f"//div[contains(text(), '{contact_name}')]"
            best_choice = self._wait_for_element_visible(contact_selector, by='xpath')
        except:

            try:
                contact_selector = f"//span[contains(text(), '{contact_name.replace('@', '')}')]"
                best_choice = self._wait_for_element_visible(contact_selector, by='xpath')

            except:
                self._wait_for_element_visible('.ChatInfo').click()
                return

        self.random_delay(3, 5)

        for element in self.driver.find_elements('xpath', contact_selector):
            self.logger.info(f'Comparing {repr(contact_name)} with {repr(element.text)}')
            best_choice = self._best_coincidence(
                expected=contact_name, first=best_choice, second=element
            )

        self.logger.info(f'Best choice is {repr(best_choice.text)}')

        self.driver.execute_script("arguments[0].scrollIntoView();", best_choice)
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, contact_selector)))
        action = ActionChains(self.driver)
        action.move_to_element(best_choice).click().perform()

        self.logger.info(f'Contact {repr(contact_name)} clicked successfully')

    @catch_timed_out
    def type_message_and_send(self, contact_name):

        self.logger.info(f'Trying to type message {repr(self.message)} and send it')
        try:
            message_input = self._wait_for_element_visible(
                'div.input-message-input[contenteditable="true"]', timeout=20
            )
        except:
            message_input = self._wait_for_element_visible(
                'div#editable-message-text', timeout=20
            )
        self.human_like_mouse_movement(message_input)
        self.update_bot_data()
        message_input.click()

        self.limit_check()

        # Typing each character of the message with random delays
        for char in self.message:
            message_input.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))
        message_input.send_keys(Keys.ENTER)
        self.random_delay()
        self.logger.info(f'Message {repr(self.message)} sent successfully to contact {repr(contact_name)}')

    @staticmethod
    def read_proxy_details(proxy_file_path):
        with open(proxy_file_path, 'r') as file:
            proxy_data = file.readline().strip()
        return proxy_data.split(':')

    def create_chromedriver(self, USER_AGENT):
        PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS = self.proxy.split(':')

        # Setting up the Chrome proxy
        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version":"22.0.0"
        }
        """

        # JavaScript for proxy authentication
        background_js = f"""
        var config = {{
            mode: "fixed_servers",
            rules: {{
                singleProxy: {{
                    scheme: "http",
                    host: "{PROXY_HOST}",
                    port: parseInt({PROXY_PORT})
                }},
                bypassList: ["localhost"]
            }}
        }};

        chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});

        function callbackFn(details) {{
            return {{
                authCredentials: {{
                    username: "{PROXY_USER}",
                    password: "{PROXY_PASS}"
                }}
            }};
        }}

        chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {{urls: ["<all_urls>"]}},
            ['blocking']
        );
        """

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        pluginfile = 'proxy_auth_plugin.zip'
        with zipfile.ZipFile(pluginfile, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)
        chrome_options.add_extension(pluginfile)
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_experimental_option("detach", True)
        chrome_options.add_argument("--mute-audio")

        if USER_AGENT:
            chrome_options.add_argument(f'--user-agent={USER_AGENT}')

        # self.user_profiles_path.mkdir(exist_ok=True, parents=True)
        # chrome_options.add_argument(f'--user-data-dir={str(self.user_profiles_path)}')

        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        service = Service(ChromeDriverManager().install())
        os.chmod(service.path, 0o755)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver

    # 3.There should be table it the DB for the message reports,was the message seen/not send/send etc.(The table should look something like:
    # bot acc - user we write to - the message we send - status of the message - counter for the messages sent to this acc).
    def save_current_message_state(self, username: str) -> None:
        with create_session() as session:
            element_dates = self.driver.find_elements('css selector', '.time-inner')

            if not element_dates:
                element_dates = self.driver.find_elements('css selector', '.peer-color-count-1 .message-time')

            ActionChains(self.driver).move_to_element(element_dates[-1]).perform()
            date = element_dates[-1].get_attribute('title')

            try:
                current_date = datetime.datetime.strptime(date, '%d %B %Y, %H:%M:%S')
            except:
                current_date = datetime.datetime.strptime(date, '%b %d, %Y, %H:%M:%S')

            session.add(
                Message(
                    profile_id=self.account_id,
                    message=self.message,
                    username=username,
                    state='sent',
                    sent_at=current_date,
                )
            )
            session.commit()
    # 3.There should be table it the DB for the message reports,was the message seen/not send/send etc.(The table should look something like:
    # bot acc - user we write to - the message we send - status of the message - counter for the messages sent to this acc).
    def update_current_messages_state(self, username: str) -> None:

        self.random_delay()
        self.logger.info(f'Updating messages state for {repr(username)}')

        with create_session() as session:

            messages = session.query(Message).where(
                Message.profile_id == self.account_id
            ).where(Message.username == username).all()

            try:
                self._wait_for_element_visible(by='css selector', selector='.is-out .time-inner')
                date_elements = self.driver.find_elements('css selector', '.is-out .time-inner')
            except:
                self._wait_for_element_visible(by='css selector', selector='.peer-color-count-1 .message-time')
                date_elements = self.driver.find_elements('css selector', '.peer-color-count-1 .message-time')

            for message in messages:

                if message.state == 'read':
                    continue

                for date_element in date_elements:

                    ActionChains(self.driver).move_to_element(date_element).perform()
                    date = date_element.get_attribute('title')

                    try:
                        current_date = datetime.datetime.strptime(date, '%d %B %Y, %H:%M:%S')
                    except:
                        current_date = datetime.datetime.strptime(date, '%b %d, %Y, %H:%M:%S')

                    try:
                        checked_symbol = self._wait_for_element_visible(
                            by='css selector', selector='.time-sending-status', extract_from=date_element
                        ).text == '\ue901'
                    except:
                        checked_symbol = bool(self._wait_for_element_visible(
                            by='xpath',
                            selector='following-sibling::div[@class="MessageOutgoingStatus"]',
                            extract_from=date_element
                        ).find_element('css selector', 'i[class*="icon-message-read"]'))

                    delta = datetime.timedelta(seconds=5)
                    start_threshold = message.sent_at - delta
                    end_threshold = message.sent_at + delta
                    time_ok = start_threshold <= current_date <= end_threshold

                    if time_ok and checked_symbol:
                        message.state = 'read'
                        break

            self.logger.info(f'Messages state for {repr(username)} updated successfully')
            session.commit()

    # 3.There should be table it the DB for the message reports,was the message seen/not send/send etc.(The table should look something like:
    # bot acc - user we write to - the message we send - status of the message - counter for the messages sent to this acc).
    @catch_logged_out
    @catch_timed_out
    @catch_limit_exceeded
    def check_messages_state(self) -> None:

        self.login_to_account()
        self.driver.refresh()
        self.update_bot_data()

        while True:

            with create_session() as session:
                usernames = session.query(Message.username).where(
                    Message.profile_id == self.account_id
                ).where(Message.state == 'sent').all()

            if len(usernames) == 0:
                break

            for username in usernames:
                self.driver.refresh()
                self.logger.info(f'Checking messages state for {repr(username)}')
                username = username[0]
                self.search_for_contact(username)
                self.click_contact(username)
                self.update_current_messages_state(username)
                self.logger.info(f'Messages state for {repr(username)} checked successfully')

            time.sleep(random.randint(60, 90))

    # 3.There should be table it the DB for the message reports,was the message seen/not send/send etc.(The table should look something like:
    # bot acc - user we write to - the message we send - status of the message - counter for the messages sent to this acc).
    def login_to_account(self) -> None:

        self.driver.get('https://web.telegram.org/')

        if os.path.exists(self.local_storage_file_path):
            self.logger.info('Local storage file found')
            self.load_local_storage(self.local_storage_file_path)
            print("Local storage loaded successfully.")

            try:
                chatlist_selector = ".animated-menu-icon"
                self.random_delay(15, 20)
                self._wait_for_element_visible(chatlist_selector)

            except (
                    TimeoutException,
                    NoSuchElementException,
                    ElementNotVisibleException
            ):
                self.logger.info('Local storage file is outdated')
                self.logger.info('Waiting for user to log in manually')
                print("Please relog in manually.")

                # Open Telegram web page for manual login
                # self.driver.get('https://web.telegram.org/')

                # Wait for user to log in manually, identified by the presence of the chat list
                chatlist_selector = ".animated-menu-icon"
                self._wait_for_element_visible(chatlist_selector, timeout=600)

                # After manual login, save the local storage
                self.random_delay(5, 10)
                self.save_local_storage(self.local_storage_file_path)
                print("Local storage saved successfully.")

        else:
            self.logger.info('Local storage file not found')
            self.logger.info('Waiting for user to log in manually')
            print("Local storage file not found. Please log in manually.")

            # Open Telegram web page for manual login
            self.driver.get('https://web.telegram.org/')

            # Wait for user to log in manually, identified by the presence of the chat list
            chatlist_selector = ".animated-menu-icon"
            self.random_delay(5, 10)
            self._wait_for_element_visible(chatlist_selector, timeout=600)

            # After manual login, save the local storage
            self.save_local_storage(self.local_storage_file_path)
            print("Local storage saved successfully.")

        self.driver.get('https://web.telegram.org/')

        if not os.path.exists(self.local_storage_file_path):
            print("Local storage file not found. Please log in manually.")
            chatlist_selector = ".stories-list"
            self._wait_for_element_visible(chatlist_selector, timeout=600)
            self.save_local_storage(self.local_storage_file_path)
            print("Local storage saved successfully.")

    # 3.There should be table it the DB for the message reports,was the message seen/not send/send etc.(The table should look something like:
    # bot acc - user we write to - the message we send - status of the message - counter for the messages sent to this acc).
    @catch_logged_out
    @catch_timed_out
    @catch_limit_exceeded
    def write_to_users(self):

        self.login_to_account()
        self.driver.refresh()
        self.update_bot_data()

        for user in self.users_list[:]:
            self.search_for_contact(user)
            self.click_contact(user)
            self.type_message_and_send(user)
            self.save_current_message_state(user)
            self.random_delay()
