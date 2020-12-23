import requests
from selenium_chrome_driver import driver
from bs4 import BeautifulSoup
from dao import AtlasDB
import datetime

# Global variables
parser = "lxml"


def main():
    print("Web Scrapping launched...")
    # season_input = input("Quelle saison ? (Format XXXX) : ")
    season_input = int("2019")
    # Open the WebBrowser
    driver.get("https://www.basketball-reference.com/leagues/")
    # Go to the wanted season stats page
    stats_table = driver.find_element_by_id("stats")
    season = stats_table.find_element_by_xpath(
        "//th[@data-stat='season' and ./a/text()='" + str(season_input - 1) + "-" + str(season_input)[2:] + "']/a")
    if(season.is_displayed()) & (season.is_enabled()):
        season.click()
    print("Season accessed")
    # Scrap all teams with players for the season
    teams = scrap_team()

    # Scrap the stats from all games
    games = scrap_games(str(season_input))

    # Scrap the stats from the whole players for whole games
    # for game in games:
    #     players_home, players_visitor = scrap_player_stats_from_game(game["home"], game["visitor"], game["csk"])

    # Close the selenium driver
    driver.close()
    print("Web Scrapping finished...")

    # Start MongoDB importing & processing
    print("MongoDB uploading and processing launched...")

    db = AtlasDB(str(season_input))

    for team in teams:
        db.add_team(team)

    for game in games:
        players_home, players_visitor = scrap_player_stats_from_game(game["home_nick"], game["visitor_nick"], game["csk"], game['date'])
        db.add_game(game)
        for stat in players_home:
            db.add_player_stats(game["csk"], stat["name"], game["home_nick"], stat)
        for stat in players_visitor:
            db.add_player_stats(game["csk"], stat["name"], game["visitor_nick"], stat)

    print("MongoDB uploading and processing finished...")


# Scrap teams from current URL
def scrap_team():
    teams = []
    req = requests.get(driver.current_url)
    soup = BeautifulSoup(req.text, parser)
    confs_standings_e = soup.find("table", {"id": "confs_standings_E"}).find_all("tr", {"class": "full_table"})
    confs_standings_w = soup.find("table", {"id": "confs_standings_W"}).find_all("tr", {"class": "full_table"})

    for row in confs_standings_e:
        team = {"nick": row.contents[0].a["href"][7:10],
                "name": row.contents[0].a.text,
                "wins": int(row.contents[1].text),
                "losses": int(row.contents[2].text),
                "win_loss_pct": float(row.contents[3].text),
                "gb": 0 if row.contents[4].text == "—" else float(row.contents[4].text),
                "pts_per_g": float(row.contents[5].text),
                "opp_pts_per_g": float(row.contents[6].text),
                "srs": float(row.contents[7].text),
                "gameIds": [],
                "rosterIds": []}

        # print(team)
        teams.append(team)

    for row in confs_standings_w:
        team = {"nick": row.contents[0].a["href"][7:10],
                "name": row.contents[0].a.text,
                "wins": int(row.contents[1].text),
                "losses": int(row.contents[2].text),
                "win_loss_pct": float(row.contents[3].text),
                "gb": 0 if row.contents[4].text == "—" else float(row.contents[4].text),
                "pts_per_g": float(row.contents[5].text),
                "opp_pts_per_g": float(row.contents[6].text),
                "srs": float(row.contents[7].text),
                "gameIds": [],
                "rosterIds": []}
        # print(team)
        teams.append(team)
    return teams


# Scrap games from team from season
def scrap_games(season):
    games = []
    driver.get("https://www.basketball-reference.com/leagues/NBA_" + season + "_games.html")

    filters = driver.find_element_by_class_name("filter")
    months = []
    for a in filters.find_elements_by_xpath(".//a"):
        months.append(a.get_attribute("href"))

    for month in months:
        driver.get(month)
        # print(month)

        req = requests.get(driver.current_url)
        soup = BeautifulSoup(req.text, parser)
        table = soup.find("table", {"id": "schedule"})

        if table is not None:
            rows = table.find("tbody").find_all("tr", {"class": None})
            for row in rows:
                game = {}

                date_th = row.find("th", {"data-stat": "date_game"})
                if date_th is not None:
                    game["csk"] = date_th["csk"]
                    date_text = date_th["csk"]
                    date_year = int(date_text[0:4])
                    date_month = int(date_text[4:6])
                    date_day = int(date_text[6:8])
                    date = datetime.datetime(date_year, date_month, date_day)
                    game["date"] = date

                game_hour = row.find("td", {"data-stat": "game_start_time"})
                if game_hour is not None:
                    game["hour"] = game_hour.text

                visitor_nick = row.find("td", {"data-stat": "visitor_team_name"})
                if visitor_nick is not None:
                    game["visitor_nick"] = visitor_nick.a["href"][7:10]

                home_nick = row.find("td", {"data-stat": "home_team_name"})
                if home_nick is not None:
                    game["home_nick"] = home_nick.a["href"][7:10]

                home_pts = row.find("td", {"data-stat": "home_pts"})
                if home_pts is not None:
                    game["home_pts"] = int(home_pts.text)

                visitor_pts = row.find("td", {"data-stat": "visitor_pts"})
                if visitor_pts is not None:
                    game["visitor_pts"] = int(visitor_pts.text)

                games.append(game)
                # print(game)

    return games


# Scrap player stats from a specific game
def scrap_player_stats_from_game(home, visitor, csk, date):
    roster_home = []
    roster_visitor = []

    # driver.get("https://www.basketball-reference.com/boxscores/"+csk+".html")
    req = requests.get("https://www.basketball-reference.com/boxscores/"+csk+".html")
    print("https://www.basketball-reference.com/boxscores/"+csk+".html")

    if req.status_code == 404:
        print("404 NOT FOUND")
        return

    soup = BeautifulSoup(req.text, parser)
    simple_table_home = soup.find("table", {"id": "box-" + home + "-game-basic"})
    simple_table_visitor = soup.find("table", {"id": "box-" + visitor + "-game-basic"})
    advanced_table_home = soup.find("table", {"id": "box-" + home + "-game-advanced"})
    advanced_table_visitor = soup.find("table", {"id": "box-" + visitor + "-game-advanced"})

    if simple_table_home is not None:
        rows = simple_table_home.find("tbody").find_all("tr", {"class": None})
        for row in rows:
            player = {}
            player_th = row.find("th", {"data-stat": "player"})
            if player_th is not None:
                player["name"] = player_th.text
                stats = row.find_all("td")
                for stat in stats:
                    if stat["data-stat"] in ["mp", "reason"]:
                        value = stat.text
                    else:
                        value = "" if stat.text == "" else (int(stat.text) if "." not in stat.text else float(stat.text))
                    player[stat["data-stat"]] = value
                roster_home.append(player)

    if advanced_table_home is not None:
        rows = advanced_table_home.find("tbody").find_all("tr", {"class": None})
        for row in rows:
            player_th = row.find("th", {"data-stat": "player"})
            if player_th is not None:
                player = next((player for player in roster_home if player["name"] == player_th.text), None)
                if player is not None:
                    stats = row.find_all("td")
                    for stat in stats:
                        if stat["data-stat"] in ["mp", "reason"]:
                            value = stat.text
                            if stat["data-stat"] == "reason":
                                injured_req = requests.get("https://www.prosportstransactions.com/basketball/Search/SearchResults.php?Player=" + player['name'] + "&Team=&BeginDate=" + str(date.year - 1) + "-" + str(date.month) + "-" + str(date.day) + "&EndDate=" + str(date.year) + "-" + str(date.month) + "-" + str(date.day) + "&ILChkBx=yes&Submit=Search")
                                soup = BeautifulSoup(injured_req.text, parser)
                                table = soup.find({"class": "datatable"})
                                if table is not None:
                                    injured_rows = table.find_all('tr', {'align': 'left'})
                                    last_entry = injured_rows[len(injured_rows) - 1]
                                    if last_entry is not None :
                                        tds = last_entry.find_all('td')
                                        if tds is not None:
                                            if(tds[3] is not None) & (tds[4] is not None):
                                                if tds[3].text != " ":
                                                    value = tds[4].text
                                                    print(value)
                                                   
                        else:
                            value = "" if stat.text == "" else (
                                int(stat.text) if "." not in stat.text else float(stat.text))
                        player[stat["data-stat"]] = value
    


    if simple_table_visitor is not None:
        rows = simple_table_visitor.find("tbody").find_all("tr", {"class": None})
        for row in rows:
            player = {}
            player_th = row.find("th", {"data-stat": "player"})
            if player_th is not None:
                player["name"] = player_th.text
                stats = row.find_all("td")
                for stat in stats:
                    if stat["data-stat"] in ["mp", "reason"]:
                        value = stat.text
                    else:
                        value = "" if stat.text == "" else (int(stat.text) if "." not in stat.text else float(stat.text))
                    player[stat["data-stat"]] = value
                roster_visitor.append(player)

    if advanced_table_visitor is not None:
        rows = advanced_table_visitor.find("tbody").find_all("tr", {"class": None})
        for row in rows:
            player_th = row.find("th", {"data-stat": "player"})
            if player_th is not None:
                player = next((player for player in roster_visitor if player["name"] == player_th.text), None)
                if player is not None:
                    stats = row.find_all("td")
                    for stat in stats:
                        if stat["data-stat"] in ["mp", "reason"]:
                            value = stat.text
                            if stat["data-stat"] == "reason":
                                injured_req = requests.get(
                                    "https://www.prosportstransactions.com/basketball/Search/SearchResults.php?Player=" +
                                    player['name'] + "&Team=&BeginDate=" + str(date.year - 1) + "-" + str(
                                        date.month) + "-" + str(date.day) + "&EndDate=" + str(date.year) + "-" + str(
                                        date.month) + "-" + str(date.day) + "&ILChkBx=yes&Submit=Search")
                                soup = BeautifulSoup(injured_req.text, parser)
                                table = soup.find({"class": "datatable"})
                                if table is not None:
                                    injured_rows = table.find_all('tr', {'align': 'left'})
                                    last_entry = injured_rows[len(injured_rows) - 1]
                                    if last_entry is not None:
                                        tds = last_entry.find_all('td')
                                        if tds is not None:
                                            if (tds[3] is not None) & (tds[4] is not None):
                                                if tds[3].text != " ":
                                                    value = tds[4].text
                                                    print(value)
                        else:
                            value = "" if stat.text == "" else (
                                int(stat.text) if "." not in stat.text else float(stat.text))
                        player[stat["data-stat"]] = value

    # print(roster_home)
    # print(roster_visitor)

    return roster_home, roster_visitor


# Entry Point for the application
if __name__ == '__main__':
    main()
