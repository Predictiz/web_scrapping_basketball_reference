import requests
from selenium_chrome_driver import driver
from bs4 import BeautifulSoup
from dao import AtlasDB
import datetime

# Global variables
parser = "lxml"


def main():
    print("Web Scrapping launched...")
    season_input = int(input("Quelle saison ? (Format XXXX) : "))
    limit_input = int(input(" match à partir duquel commencez le scrapping  (0 pour commencer au début): "))
    # season_input = int("2019")
    # Open the WebBrowser
    driver.get("https://www.basketball-reference.com/leagues/")
    # Go to the wanted season stats page
    stats_table = driver.find_element_by_id("stats")
    season = stats_table.find_element_by_xpath(
        "//th[@data-stat='season' and ./a/text()='" + str(season_input - 1) + "-" + str(season_input)[2:] + "']/a")
    if(season.is_displayed()) & (season.is_enabled()):
        try:
            season.click()
        except Exception:
            driver.implicitly_wait(5)
            season.click()
    print("Season accessed")
    # Scrap all teams with players for the season
    teams = scrap_team(season_input)

    # Scrap the stats from all games
    games = scrap_games(str(season_input), teams)

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

    i = 1
    for game in games:
        if(i > limit_input):
            players_home, players_visitor = scrap_player_stats_from_game(game["home_nick"], game["visitor_nick"], game["csk"], game['date'])
            db.add_game(game)
            for stat in players_home:
                db.add_player_stats(game["csk"], stat["name"], game["home_nick"], stat)
            for stat in players_visitor:
                db.add_player_stats(game["csk"], stat["name"], game["visitor_nick"], stat)
        i +=1

    print("MongoDB uploading and processing finished...")


def daily_scrapping():

    print("Daily Scrapping launched...")
    season_input = 2021
    # season_input = int("2019")
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
    teams = scrap_team(season_input)

    # Scrap the stats from all games
    games = scrap_games(str(season_input), teams)

    # Close the selenium driver
    driver.close()
    print("Web Scrapping finished...")

    # Start MongoDB importing & processing
    print("MongoDB uploading and processing launched...")

    db = AtlasDB(str(season_input))

    for team in teams:
        db.add_team(team)

    today = datetime.date.today()
    time_delta = datetime.timedelta(2)
    minimum_date = today - time_delta
    print(today, minimum_date)
    for game in games:
        if(game['date'].date() <= today) & (game['date'].date() > minimum_date):
            print(game['date'].date())
            db.add_game(game)
            if(game['not_played'] == False):
                players_home, players_visitor = scrap_player_stats_from_game(game["home_nick"], game["visitor_nick"], game["csk"], game['date'])
                for stat in players_home:
                    db.add_player_stats(game["csk"], stat["name"], game["home_nick"], stat)
                for stat in players_visitor:
                    db.add_player_stats(game["csk"], stat["name"], game["visitor_nick"], stat)
            

    print("MongoDB uploading and processing finished...")



# Scrap teams from current URL
def scrap_team(season):
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

    if(season <= 2017):
        season_year = 2017
    else:
        season_year = season -1
    url = requests.get("https://projects.fivethirtyeight.com/"+ str(season_year)+"-nba-predictions/")
    soup = BeautifulSoup(url.text,parser)
    rows_rating = soup.find("table", {"id":"standings-table"}).find("tbody").find_all("tr")
    for row_rating in rows_rating:
        if(row_rating != None):
            team_cell = row_rating.find('td',{'class': "team"})
            team_nick = team_cell['data-str'].split()
            for team in teams:
                splitted_name = team['name'].split()
                nick = splitted_name[len(splitted_name)-1]
                if(nick == team_nick[len(team_nick)-1]):
                    team['elo_score'] = int(row_rating.find('td').text)
                    team['elo_before_game'] = int(row_rating.find('td').text)
    return teams


# Scrap games from team from season
def scrap_games(season, teams):
    today = datetime.datetime.today()
    time_delta = datetime.timedelta(1)
    today = today - time_delta
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
                has_not_happened = True

                date_th = row.find("th", {"data-stat": "date_game"})
                if date_th is not None:
                    game["csk"] = date_th["csk"]
                    date_text = date_th["csk"]
                    date_year = int(date_text[0:4])
                    date_month = int(date_text[4:6])
                    date_day = int(date_text[6:8])
                    date = datetime.datetime(date_year, date_month, date_day)
                    game["date"] = date
                    if(date < today):
                        has_not_happened = False

                
                game['not_played'] = has_not_happened


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
                if (home_pts is not None) & (has_not_happened == False):
                    game["home_pts"] = int(home_pts.text)

                visitor_pts = row.find("td", {"data-stat": "visitor_pts"})
                if (visitor_pts is not None) & (has_not_happened == False):
                    game["visitor_pts"] = int(visitor_pts.text)

                overtime = row.find("td", {"data-stat": "overtimes"})
                if (overtime is not None) & (has_not_happened == False):
                    if(overtime.text != "") &(overtime.text != " "):
                        game["overtime"] = True
                    else:
                        game["overtime"] = False
                
                attendance = row.find("td", {"data-stat": "attendance"})
                if (attendance is not None) & (has_not_happened == False):
                    if attendance.text is not None:
                        if attendance.text != "":
                            game["attendance"] = int(attendance.text.replace(",", ""))
                        else:
                            game["attendance"] = 0

                games.append(game)
                # print(game)
    print("getting odds for games")
    games_odds = get_game_odds()
    print("done")
    for game in games:
        for team in teams:
            if(team['nick'] == game['home_nick']):
                home_team = team
            elif (team['nick'] == game['visitor_nick']):
                visitor_team = team


        if(home_team != None) & (visitor_team != None):
                game['home_elo_before_game'] = home_team['elo_before_game']
                game['visitor_elo_before_game'] = visitor_team['elo_before_game']

                if(game['not_played'] == False):
                    # si victoire de l'equipe home
                    if(game['home_pts'] > game['visitor_pts']):
                        game['winner'] = 1
                        p_win = 1/(1 + pow(10., -(home_team['elo_before_game'] - visitor_team['elo_before_game'])/400))
                        delta = 20*(1 - p_win)
                        home_team['elo_before_game'] = home_team['elo_before_game'] + delta
                        visitor_team['elo_before_game'] = visitor_team['elo_before_game'] - delta

                    # si égalité ou défaite de l'équipe home
                    else:
                        game['winner'] = 0
                        p_win = 1/(1 + pow(10., -(visitor_team['elo_before_game'] - home_team['elo_before_game'])/400))
                        delta = 20*(1 - p_win)
                        home_team['elo_before_game'] = home_team['elo_before_game'] - delta
                        visitor_team['elo_before_game'] = visitor_team['elo_before_game'] + delta

                #Si le match n'a pas été joué, on va chercher sa côte      
                else:
                    game['home_odd'] = 1
                    game['visitor_odd'] = 1
                    for game_odds in games_odds:
                        if(game_odds["home_team"] == home_team["name"]) & (game_odds["visitor_team"] == visitor_team["name"]):
                            game['home_odd'] = game_odds['home_odd']
                            game['visitor_odd'] = game_odds['visitor_odd']
                        

    
    for team in teams:
        team.pop('elo_before_game', None)

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
        post = 0
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
                if(post < 5):
                    player["started"] = 1 
                else:
                    player["started"] = 0
                post +=1
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
                            if stat["data-stat"] == "mp":
                                time_played= stat.text.split(":")
                                minute_played = int(time_played[0])
                                second_played = (int(time_played[1])) / 60
                                value = minute_played + second_played
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
        post = 0
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
                if(post < 5):
                    player["started"] = 1 
                else:
                    player["started"] = 0
                post +=1
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
                            if stat["data-stat"] == "mp":
                                time_played= stat.text.split(":")
                                minute_played = int(time_played[0])
                                second_played = (int(time_played[1])) / 60
                                value = minute_played + second_played
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


def get_game_odds():
    req = requests.get("https://www.wincomparator.com/fr-fr/cotes/basket/usa/nba-id306/")
    soup = BeautifulSoup(req.text, "lxml")
    rows = soup.find_all("div",{"class":"event__item__odd"})
    games_odd = []
    for row in rows:
        game = {
            "home_odd" :1,
            "visitor_odd":1,
        }
        div_home = row.find("span", {"class":"mr-2"})
        if(div_home != None):
            game['home_team'] = div_home.text

        div_visitor = row.find("span", {"class":"ml-2"})
        if(div_visitor != None):
            game['visitor_team'] = div_visitor.text

        odd_div = row.find_all("a", {"class":"event__item__odd"})
        if(odd_div != None):
            if(len(odd_div) >= 2):
                div_home_odd = odd_div[0].find('span')
                div_visitor_odd = odd_div[1].find('span')
                if(div_home_odd != None):
                    game["home_odd"] = float(div_home_odd.text)
                if(div_visitor_odd != None):
                    game["visitor_odd"] = float(div_visitor_odd.text)

        games_odd.append(game)

    return games_odd


# Entry Point for the application
if __name__ == '__main__':
    daily_scrapping()
