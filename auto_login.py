from seleniumbase import BaseCase
import os
import time
import random
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
        search_input.send_keys(contact_name)

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

        # Focus on the message input div and type the message
        self.human_like_mouse_movement(message_input)
        message_input.click()
        message_input.send_keys(message)

        # Press Enter to send the message
        message_input.send_keys(Keys.ENTER)

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

        # Search for the contact name
        self.search_for_contact("@absolutunit3")

        # Click on the specific contact after searching
        self.click_contact("Nikola Krivulev")

        # Type a message and send it
        self.type_message_and_send("Hello")

        input("Press Enter to close the browser...")

if __name__ == "__main__":
    import pytest
    pytest.main(args=["-s", "auto_login.py"])
