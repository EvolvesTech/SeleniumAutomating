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
        
        # Wait for the search input field to be visible and clickable
        search_input = self.wait_for_element_visible(search_input_selector)
        
        # Move the mouse to the search input field and click on it
        self.human_like_mouse_movement(search_input)
        search_input.click()

        # Clear any existing text and input the desired contact name
        search_input.clear()

        # Simulate human-like typing for the contact name
        for char in contact_name:
            search_input.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3)) 

    def click_contact(self, contact_name):
        contact_selector = f"//span[contains(text(), '{contact_name}')]"
        contact_element = self.wait_for_element_visible(contact_selector)

        # Scroll to the element's position
        self.driver.execute_script("arguments[0].scrollIntoView();", contact_element)

        # Wait for the element to be clickable
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, contact_selector)))

        # Click using ActionChains
        action = ActionChains(self.driver)
        action.move_to_element(contact_element).click().perform()

    def type_message_and_send(self, message):
        message_input_selector = 'div.input-message-input[contenteditable="true"]'  # Adjust if necessary
        message_input = self.wait_for_element_visible(message_input_selector)

        # Focus on the message input div
        self.human_like_mouse_movement(message_input)
        message_input.click()

        # Simulate human-like typing
        for char in message:
            message_input.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))  # Adjust the delay range as needed

        # Press Enter to send the message
        message_input.send_keys(Keys.ENTER)

    def create_chromedriver(self, PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS, USER_AGENT):
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
        
        def get_chromedriver(use_proxy=True, user_agent=USER_AGENT):
            chrome_options = webdriver.ChromeOptions()
            if use_proxy:
                pluginfile = 'proxy_auth_plugin.zip'
                with zipfile.ZipFile(pluginfile, 'w') as zp:
                    zp.writestr("manifest.json", manifest_json)
                    zp.writestr("background.js", background_js)
                chrome_options.add_extension(pluginfile)
                chrome_options.add_argument("--start-maximized")
                chrome_options.add_experimental_option("detach", True)
                chrome_options.add_argument("--mute-audio")
            if user_agent:
                chrome_options.add_argument(f'--user-agent={user_agent}')
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            return driver

        driver = get_chromedriver(use_proxy=True)
        return driver
    
    def test_telegram_login_with_proxy(self):
        local_storage_file_path = "local_storage.json"

        # Proxy details - Change these to match your proxy settings
        PROXY_HOST = "your_proxy_host"
        PROXY_PORT = "your_proxy_port"
        PROXY_USER = "your_proxy_username"
        PROXY_PASS = "your_proxy_password"

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

        # Search for the contact name
        self.search_for_contact("@nkrivulev")

        # Click on the specific contact after searching
        self.click_contact("Nikola Krivulev")

        # Type a message and send it
        self.type_message_and_send("Hello")

        input("Press Enter to close the browser...")

if __name__ == "__main__":
    import pytest
    pytest.main(args=["-s", "auto_login.py"])