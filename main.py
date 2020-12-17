from selenium_chrome_driver import driver


def main():
    print("Web Scrapping Launched...")
    # Open the WebBrowser
    driver.get("https://www.basketball-reference.com/leagues/")
    # Go to the wanted season stats page
    stats_table = driver.find_element_by_id("stats")
    season = stats_table.find_element_by_xpath("//th[@data-stat='season' and ./a/text()='2019-20']/a")
    season.click()
    print("Season accessed")
    # Scrap the stats from the whole teams
    # TODO : SCRAP

    # Scrap the stats from the whole players
    # TODO : SCRAP

    # Close the selenium driver
    driver.close()
    print("Web Scrapping finished...")


# Entry Point for the application
if __name__ == '__main__':
    main()
