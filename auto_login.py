# Importing necessary libraries
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

# Defining a class for Telegram Login Test
class TelegramLoginTest(BaseCase):

    # Method to set up the test environment
    def setUp(self):
        super(TelegramLoginTest, self).setUp()
        # Custom user-agent to mimic a real browser
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
        })
        # Adding randomized behavior to avoid detection as a bot
        self.add_random_behavior()

    # Method to add scripts to the browser to make it appear more like a normal user
    def add_random_behavior(self):
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

    # Method to save the browser's local storage to a file
    def save_local_storage(self, path):
        local_storage = self.driver.execute_script("return JSON.stringify(localStorage);")
        with open(path, 'w') as file:
            file.write(local_storage)

    # Method to load local storage from a file into the browser
    def load_local_storage(self, path):
        with open(path, 'r') as file:
            local_storage = file.read()
        self.driver.execute_script("localStorage.clear(); var data = JSON.parse(arguments[0]); for (var key in data) localStorage.setItem(key, data[key]);", local_storage)

    # Method to search for a contact in Telegram
    def search_for_contact(self, contact_name):
        search_input_selector = ".input-field-input.input-search-input"  # Selector for the search input field
        search_input = self.wait_for_element_visible(search_input_selector)
        self.human_like_mouse_movement(search_input)
        search_input.click()
        search_input.clear()
        # Typing each character of the contact name with random delays
        for char in contact_name:
            search_input.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))

    # Method to click on a contact after searching
    def click_contact(self, contact_name):
        contact_selector = f"//div[contains(text(), '{contact_name}')]"
        contact_element = self.wait_for_element_visible(contact_selector)
        self.driver.execute_script("arguments[0].scrollIntoView();", contact_element)
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, contact_selector)))
        action = ActionChains(self.driver)
        action.move_to_element(contact_element).click().perform()

    # Method to type a message and send it
    def type_message_and_send(self, message):
        message_input_selector = 'div.input-message-input[contenteditable="true"]'  # Selector for the message input
        message_input = self.wait_for_element_visible(message_input_selector)
        self.human_like_mouse_movement(message_input)
        message_input.click()
        # Typing each character of the message with random delays
        for char in message:
            message_input.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))
        message_input.send_keys(Keys.ENTER)

    # Method to read proxy details from a file
    def read_proxy_details(self, proxy_file_path):
        with open(proxy_file_path, 'r') as file:
            proxy_data = file.read().strip()
        return proxy_data.split(':')

    # Method to create a ChromeDriver instance with specific proxy settings
    def create_chromedriver(self, proxy_file_path, USER_AGENT):
        PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS = self.read_proxy_details(proxy_file_path)

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

        # Configuring Chrome options for the driver
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
        
        # Creating and returning the ChromeDriver instance
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver

    # Main test method for logging in to Telegram with a proxy
    def test_telegram_login_with_proxy(self):
        local_storage_file_path = "local_storage.json"
        proxy_file_path = "proxies.txt"  # Path to your proxies.txt file

        # Creating a ChromeDriver with proxy settings
        self.driver = self.create_chromedriver(proxy_file_path, USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36")

        # Navigating to the Telegram web page
        self.open('https://web.telegram.org/')

        # Loading local storage if available
        if os.path.exists(local_storage_file_path):
            self.load_local_storage(local_storage_file_path)
            print("Local storage loaded successfully.")
        else:
            print("Local storage file not found. Please log in manually.")

            # Open Telegram web page for manual login
            self.open('https://web.telegram.org/')
            
            # Wait for user to log in manually, identified by the presence of the chat list
            chatlist_selector = ".stories-list"
            self.wait_for_element_visible(chatlist_selector, timeout=600)
            
            # After manual login, save the local storage
            self.save_local_storage(local_storage_file_path)
            print("Local storage saved successfully.")
        # Reopening Telegram web page
        self.open('https://web.telegram.org/')

        # Handling first-time login by manually logging in and saving local storage
        if not os.path.exists(local_storage_file_path):
            print("Local storage file not found. Please log in manually.")
            chatlist_selector = ".stories-list"
            self.wait_for_element_visible(chatlist_selector, timeout=600)
            self.save_local_storage(local_storage_file_path)
            print("Local storage saved successfully.")

        # Searching and contacting a specific user
        self.search_for_contact("@Sasho")
        self.click_contact("@Sasho")
        self.type_message_and_send("Hello, are you interested in marketing?")

        # Pausing execution to allow for manual interaction if necessary
        input("Press Enter to close the browser...")

# Main execution point when the script is run directly
if __name__ == "__main__":
    import pytest
    pytest.main(args=["-s", "auto_login.py"])
