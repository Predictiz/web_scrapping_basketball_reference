from pymongo import MongoClient
import os

class AtlasDB:
    def __init__(self):
        self.client = MongoClient( os.environ['PREDICTIZ_CREDENTIALS'])
        db = self.client['predictiz']
        self.tableTeam = db['team']
        self.tablePlayer = db['player']
        self.tableGame = db['game']
        self.tablePlayerStats = db['playerStats']
        print("connected")

        
    
    def addTeam(self, name, nick):
        self.tableTeam.insert_one({'name':name, 'nick':nick})
    
    def addGame(self, csk, date , hour, visitorName, homeName, visitor_pts, home_pts):
        visitor = self.tableTeam.find_one({'nick':visitorName})
        home = self.tableTeam.find_one({'nick':homeName})
        if(visitor != None) & (home!= None):
            self.tableGame.insert_one({'csk': csk, 'date': date, 'hour': hour, 'visitor': visitor['_id'], 'home': home['_id'], 'homePts': home_pts, 'visitorPts': visitor_pts})
            ("game added to the db")

    
    def addPlayer(self, name):
        exist = self.tablePlayer.find_one({'name':name})
        if(exist == None ):
            retour = self.tablePlayer.insert_one({'name' :name})
            return retour.inserted_id
        else: 
            return None

    def addPlayerStat(self, game_csk, player_name, teamName, stats ):
        team = self.tableTeam.find_one({'nick': teamName})
        game = self.tableGame.find_one({'csk':game_csk})
        player = self.tablePlayer.find_one({'nick':player_name})
        if player == None:
            playerId = self.addPlayer(player_name)
        else:
            playerId = player['_id']


        if(team != None) & (game != None):
            self.tablePlayerStats.insert_one({'player_id':playerId, 'game_id':game['_id'], 'team_id':team['_id'], 'stats':stats})
            print("stat added To the db")
    
