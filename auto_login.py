from seleniumbase import BaseCase
import os
import time
import random
import json
from selenium.webdriver.common.action_chains import ActionChains

class TelegramLoginTest(BaseCase):
    def setUp(self):
        super(TelegramLoginTest, self).setUp()
        # Setting a custom user-agent
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
        })
        # Adding randomized behavior
        self.add_random_behavior()

    def add_random_behavior(self):
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.execute_script("window.navigator.chrome = {runtime: {}}")
        self.driver.execute_script("window.navigator.plugins = [1, 2, 3, 4, 5]")
        self.driver.execute_script("window.navigator.languages = ['en-US', 'en']")

    def random_delay(self, min_seconds=2, max_seconds=5):
        time.sleep(random.uniform(min_seconds, max_seconds))

    def human_like_mouse_movement(self, element):
        action = ActionChains(self.driver)
        action.move_to_element(element).perform()
        self.random_delay()

    def save_local_storage(self, path):
        local_storage = self.driver.execute_script("return JSON.stringify(localStorage);")
        with open(path, 'w') as file:
            file.write(local_storage)

    def load_local_storage(self, path):
        with open(path, 'r') as file:
            local_storage = file.read()
        self.driver.execute_script("localStorage.clear(); var data = JSON.parse(arguments[0]); for (var key in data) localStorage.setItem(key, data[key]);", local_storage)

    def test_telegram_login(self):
        local_storage_file_path = "local_storage.json"
        self.open('https://web.telegram.org/')

        # Load local storage if it exists
        if os.path.exists(local_storage_file_path):
            self.load_local_storage(local_storage_file_path)
            print("Local storage loaded successfully.")

        # Open the page again to apply local storage
        self.open('https://web.telegram.org/')

        # If no saved local storage, perform login and save it
        if not os.path.exists(local_storage_file_path):
            print("Local storage file not found. Please log in manually.")
            chatlist_selector = ".stories-list"
            self.wait_for_element_visible(chatlist_selector, timeout=600)
            self.save_local_storage(local_storage_file_path)
            print("Local storage saved successfully.")

        input("Press Enter to close the browser...")

if __name__ == "__main__":
    import pytest
    pytest.main(args=["-s", "auto_login.py"])
