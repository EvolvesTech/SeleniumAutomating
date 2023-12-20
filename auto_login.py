import os
import time
import random
import zipfile
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from seleniumbase import BaseCase
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

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

    def search_for_contact(self, contact_name):
        search_input_selector = ".input-field-input.input-search-input"  # Replace with your selector
        search_input = self.wait_for_element_visible(search_input_selector)
        self.human_like_mouse_movement(search_input)
        search_input.click()
        search_input.clear()
        for char in contact_name:
            search_input.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))

    def click_contact(self, contact_name):
        contact_selector = f"//span[contains(text(), '{contact_name}')]"
        contact_element = self.wait_for_element_visible(contact_selector)
        self.driver.execute_script("arguments[0].scrollIntoView();", contact_element)
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, contact_selector)))
        action = ActionChains(self.driver)
        action.move_to_element(contact_element).click().perform()

    def type_message_and_send(self, message):
        message_input_selector = 'div.input-message-input[contenteditable="true"]'  # Adjust if necessary
        message_input = self.wait_for_element_visible(message_input_selector)
        self.human_like_mouse_movement(message_input)
        message_input.click()
        for char in message:
            message_input.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))
        message_input.send_keys(Keys.ENTER)

    def read_proxy_details(self, proxy_file_path):
        with open(proxy_file_path, 'r') as file:
            proxy_data = file.read().strip()
        return proxy_data.split(':')

    def create_chromedriver(self, proxy_file_path, USER_AGENT):
        PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS = self.read_proxy_details(proxy_file_path)

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
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver

    def test_telegram_login_with_proxy(self):
        local_storage_file_path = "local_storage.json"
        proxy_file_path = "proxies.txt"  # Path to your proxies.txt file

        self.driver = self.create_chromedriver(proxy_file_path, USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36")

        self.open('https://web.telegram.org/')

        if os.path.exists(local_storage_file_path):
            self.load_local_storage(local_storage_file_path)
            print("Local storage loaded successfully.")

        self.open('https://web.telegram.org/')

        if not os.path.exists(local_storage_file_path):
            print("Local storage file not found. Please log in manually.")
            chatlist_selector = ".stories-list"
            self.wait_for_element_visible(chatlist_selector, timeout=600)
            self.save_local_storage(local_storage_file_path)
            print("Local storage saved successfully.")

        self.search_for_contact("@nkrivulev")
        self.click_contact("Nikola Krivulev")
        self.type_message_and_send("Hello, are you interested in marketing?")

        input("Press Enter to close the browser...")

if __name__ == "__main__":
    import pytest
    pytest.main(args=["-s", "auto_login.py"])
