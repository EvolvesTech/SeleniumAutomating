from seleniumbase import BaseCase
import os
import time
import random
import json
from selenium.webdriver.common.action_chains import ActionChains
import undetected_chromedriver as uc
import zipfile

class TelegramLoginTest(BaseCase):
    def setUp(self):
        super(TelegramLoginTest, self).setUp()
        PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS = self.get_first_proxy()
        USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
        self.driver = self.create_chromedriver(PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS, USER_AGENT)
        self.add_random_behavior()

    def get_first_proxy(self):
        with open('proxies.txt') as f:
            proxy = f.readline().strip()
        return proxy.split(':')

    def create_chromedriver(self, PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS, USER_AGENT):
        chromedriver_path = "C:\\Users\\EVLVSDEV2\\Desktop\\SeleniumAutomation\\chromedriver.exe"
        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Proxy Auth Extension",
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

        pluginfile = 'proxy_auth_plugin.zip'
        with zipfile.ZipFile(pluginfile, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)

        options = uc.ChromeOptions()
        options.add_extension(pluginfile)
        options.add_argument(f'--user-agent={USER_AGENT}')
        # Set the path to the ChromeDriver executable
        driver = uc.Chrome(executable_path=chromedriver_path, options=options)
        return driver

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
        try:
            local_storage = self.driver.execute_script("return JSON.stringify(localStorage);")
            if local_storage:
                with open(path, 'w') as file:
                    file.write(local_storage)
                print("Local storage saved successfully.")
            else:
                print("No data in local storage to save.")
        except Exception as e:
            print(f"Error saving local storage: {e}")

    def load_local_storage(self, path):
        with open(path, 'r') as file:
            local_storage = file.read()
        self.driver.execute_script("localStorage.clear(); var data = JSON.parse(arguments[0]); for (var key in data) localStorage.setItem(key, data[key]);", local_storage)

    def test_telegram_login(self):
        local_storage_file_path = "local_storage.json"
        # Open Google
        self.open('https://www.google.com/')
       
    input("Press Enter to close the browser...")

if __name__ == "__main__":
    import pytest
    pytest.main(args=["-s", "auto_login.py"])
