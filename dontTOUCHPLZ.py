import os
import zipfile
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from seleniumbase import BaseCase

class MyTestClass(BaseCase):

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

    def test_google_search_with_proxy(self):
        iphone_user_agent = (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 13_3 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.4 "
            "Mobile/15E148 Safari/604.1"
        )

        # Proxy details - Change these to match your proxy settings
        PROXY_HOST = "your_proxy_host"
        PROXY_PORT = "your_proxy_port"
        PROXY_USER = "your_proxy_username"
        PROXY_PASS = "your_proxy_password"

        driver = self.create_chromedriver(PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS, iphone_user_agent)
        driver.get("https://www.google.com/")
        self.sleep(1000)  # Wait for 1 second
        driver.quit()

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

    def test_google_search(self):
        iphone_user_agent = (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 13_3 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.4 "
            "Mobile/15E148 Safari/604.1"
        )

        proxies = []
        with open('proxies.txt') as f:
            for line in f:
                proxies.append(line.strip())

        for proxy in proxies:
            PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS = proxy.split(':')
            driver = self.create_chromedriver(PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS, iphone_user_agent)
            driver.get("https://www.google.com/")
            self.sleep(1000)  # Wait for 1 second
            driver.quit()

if __name__ == "__main__":
    import pytest
    pytest.main(args=["-s", "dontTOUCHPLZ.py"])
