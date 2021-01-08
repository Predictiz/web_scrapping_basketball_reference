from pymongo import MongoClient
import os
import time


class AtlasDB:
    def __init__(self, season):
        self.client = MongoClient(os.environ["PREDICTIZ_CREDENTIALS"])
        dblist = self.client.list_database_names()
        if "season_" + season in dblist:
            #raise IOError("Cette base de donnée existe déjà.")
            print("attention, cette base de donnée existe déja, vous avez 5 secondes pour annuler l'opération")
            time.sleep(5)
        db = self.client["season_" + season]
        self.table_team = db["team"]
        self.table_player = db["player"]
        self.table_game = db["game"]
        self.table_player_stats = db["playerStats"]
        print("Atlas MongoDB connected")

    def add_team(self, team):
        exist = self.table_team.find_one({"nick": team['nick']})
        if(exist == None):
            self.table_team.insert_one(team)

    def add_game(self, game):
        visitor = self.table_team.find_one({"nick": game["visitor_nick"]})
        home = self.table_team.find_one({"nick": game["home_nick"]})
        existing_game = self.table_game.find_one({"csk": game["csk"]})
        # Insert in Games
        if(existing_game is not None):
            try:
                game["home_odd"] = existing_game["home_odd"]
                game["visitor_odd"] = existing_game["visitor_odd"]
            except Exception:
                print("no odd for this game")
                game["home_odd"] = 1
                game["visitor_odd"] = 1
            self.table_game.delete_one({"csk": game["csk"]})

        if (visitor is not None) & (home is not None):
            game["visitor_id"] = visitor["_id"]
            game["home_id"] = home["_id"]
            retour = self.table_game.insert_one(game)

            # Update GamesIds in team
            self.table_team.update_one({"nick": game["visitor_nick"]}, {"$push": {"gameIds": retour.inserted_id}})
            self.table_team.update_one({"nick": game["home_nick"]}, {"$push": {"gameIds": retour.inserted_id}})

    def add_player(self, name):
        exist = self.table_player.find_one({"name": name})
        if exist is None:
            retour = self.table_player.insert_one({"name": name})
            return retour.inserted_id
        else:
            return exist['_id']

    def add_player_stats(self, game_csk, player_name, team_name, stats):
        team = self.table_team.find_one({"nick": team_name})
        game = self.table_game.find_one({"csk": game_csk})
        player = self.table_player.find_one({"name": player_name})
        if player is None:
            player_id = self.add_player(player_name)
            # print("PLAYER IS NONE, ADD PLAYER : "+str(player_id))
        else:
            player_id = player["_id"]
            # print("PLAYER IS NOT NONE, get id : "+str(player_id))

        
        if (team is not None) & (game is not None):
            # Insert in Player Stats
            self.table_player_stats.insert_one(
                {"player_id": player_id, "game_id": game["_id"], "team_id": team["_id"], "stats": stats})
            # print("stat added To the db")

            # Update rosterIds from the team if necessary
            roster_ids = team["rosterIds"]
            if player_id not in roster_ids:
                self.table_team.update_one({"nick": team_name}, {"$push": {"rosterIds": player_id}})
