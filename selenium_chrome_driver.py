from selenium import webdriver

options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')
options.add_argument('--incognito')
options.add_argument('--headless')
# driver = webdriver.Chrome("../chromedriver", chrome_options=options)
driver = webdriver.Chrome("../chromedriver.exe", chrome_options=options)
