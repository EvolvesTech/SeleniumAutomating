# import pickle
# import undetected_chromedriver as uc
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.wait import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# import time

# if __name__ == '__main__':

#     options = webdriver.ChromeOptions()
#     # options.add_argument('proxy-server=106.122.8.54:3128')
#     # options.add_argument(r'--user-data-dir=C:\Users\suppo\AppData\Local\Google\Chrome\User Data\Default')

#     browser = uc.Chrome(options=options)
#     browser.get('https://accounts.google.com/signin/v2/identifier?continue=https%3A%2F%2Fmail.google.com%2Fmail%2F&service=mail&sacu=1&rip=1&hl=en&flowName=GlifWebSignIn&flowEntry=ServiceLogin')

#     # Wait for user to manually enter email and password
#     input("Please log in manually and then press Enter here...")

#     # Wait for the login process to complete
#     WebDriverWait(browser, 10).until(
#         EC.visibility_of_element_located((By.CSS_SELECTOR, '#passwordNext > div > button > span')))

#     time.sleep(5)

#     # Save cookies after login
#     cookies = browser.get_cookies()
#     pickle.dump(cookies, open("cookies.pkl", "wb"))
