from selenium import webdriver
from sys import platform

options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')
options.add_argument('--incognito')
options.add_argument('--headless')
if platform == "win32":
    driver = webdriver.Chrome("../chromedriver.exe", chrome_options=options)
else:
    driver = webdriver.Chrome("../chromedriver", chrome_options=options)
