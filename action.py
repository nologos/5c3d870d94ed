import json
import requests


def wfile(var):
    writevartofile = open("tempvar.json", "w")
    writevartofile.write(json.dumps(var))
    writevartofile.close()


class Match:
    def __init__(self, matchid,playerrank, winner, looser, winner_efficiency, looser_efficiency):
        self.matchid = matchid
        self.playerrank = playerrank
        self.winner = winner
        self.looser = looser
        self.winner_efficiency = winner_efficiency
        self.looser_efficiency = looser_efficiency
    def to_dict(self):
        return {
            'matchid': self.matchid,
            'playerrank': self.playerrank,
            'winner': self.winner,
            'looser': self.looser,
            'winner_efficiency': self.winner_efficiency,
            'looser_efficiency': self.looser_efficiency
        }


class mid_matchup():
    def __init__(self, matchid):
        self.matchid = matchid
        self.isParsed = None
        self.match_data = self.get_match_data(matchid)
        self.matchrank = 75
        self.mid_players = []
        self.winner = None
        self.loser = None
        self.matchup = None
        self.loosinghero = None
        self.winninghero = None
        if self.isParsed:
            self.mid_lane_matchup()
            self.get_winner()
            self.get_matchrank()   
    def mid_lane_matchup(self):
        if self.match_data:
            for player in self.match_data['players']:
                if player['lane_role'] == 2:  # 2 is mid lane
                    self.mid_players.append(player)
            self.mid_players.sort(key=lambda player: player['hero_id'], reverse=False)
            if self.mid_players:
                # print(f"Number of players who participated in mid lane: {len(self.mid_players)}")
                self.matchup = (self.mid_players[0]['hero_id'], self.mid_players[1]['hero_id'])
        else:
            print("No players participated in mid lane.")
    def get_winner(self):
        if self.mid_players:
            self.mid_players.sort(key=lambda player: player['hero_id'], reverse=False)
            self.matchup = (self.mid_players[0]['hero_id'], self.mid_players[1]['hero_id'])
            self.mid_players.sort(key=lambda player: player['lane_efficiency_pct'], reverse=True)
            self.winner = self.mid_players[0]
            self.loser = self.mid_players[1]
        else:
            print("No players participated in mid lane.")
    def matchup_analysis(self,player1):
        # player2 is mid_players that is not player1
        player2 = [x for x in mid_players if x != player1][0]
        # calculate difference
        print(player1['lane_efficiency_pct'])
        print(player2['lane_efficiency_pct'])
        difference = player1['lane_efficiency_pct'] - player2['lane_efficiency_pct']
        # calculate win, lose or draw if difference is >5%
        if abs(difference) > 5:
            if difference > 0:
                result = f"Player with hero ID {player1['hero_id']} won the matchup."
            else:
                result = f"Player with hero ID {player1['hero_id']} lost the matchup."
        else:
            result = "The matchup was a draw."
        # calculate if lane was good or bad if efficiency below 60%
        if player1['lane_efficiency_pct'] < 60:
            lane_quality_player1 = "bad"
        else:
            lane_quality_player1 = "good"
        if player2['lane_efficiency_pct'] < 60:
            lane_quality_player2 = "bad"
        else:
            lane_quality_player2 = "good"
        return result, lane_quality_player1, lane_quality_player2
    def get_matchrank(self):
        if self.match_data:
            valid_ranks = [player['rank_tier'] for player in self.match_data["players"] if player['rank_tier'] is not None and player['rank_tier'] > 0]
            if valid_ranks:
                average_rank = sum(valid_ranks) / len(valid_ranks)
                return average_rank
            else:
                return "poop"
        else:
            return "Poop"
    __str__ = lambda self: f"Match ID: {self.matchid}, Matchup: {self.matchup}, Winner: {self.winner['hero_id']}, Loser: {self.loser['hero_id']}, Match Rank: {self.matchrank()}"
    def retunformatch(self):
        return self.matchid, self.matchrank, self.winner['hero_id'], self.loser['hero_id'], self.winner['lane_efficiency_pct'], self.loser['lane_efficiency_pct']
    def get_match_data(self, match_id):
        response = requests.get(f"https://api.opendota.com/api/matches/{match_id}")
        if response.status_code == 200:
            #if jsonload contain version returns a keyerror 
            try:
                json.loads(response.text)["version"]
                self.isParsed = True
            except KeyError:
                self.isParsed = False
            return json.loads(response.text)
        elif response.status_code == 429:
            print("daily api limit exceeded")
        else:
            print("failed to fetch match data")
            return None



class Match_numbers:
    def __init__(self,minrank=75):
        self.data = []
        self.min_rank = minrank
    def get_public_matches(self, less_than_match_id=None):
        url = "https://api.opendota.com/api/publicMatches"
        params = {}
        if self.min_rank is not None:
            params['min_rank'] = self.min_rank
        if less_than_match_id is not None:
            params['less_than_match_id'] = less_than_match_id
        response = requests.get(url, params=params)
        data = response.json()
        # you need to use extend because the returned data is a list
        # if returned data was a single entity you would use append
        self.data.extend(data)
    def get_more(self):
        if self.data:
            last_match_id = self.data[-1]['match_id']
            self.get_public_matches(less_than_match_id=last_match_id)
    def len(self):
        if self.data:
            return len(self.data)
    def vet_data(self):
        # remove stopms and non AP games
        self.data = [match for match in self.data if match['duration'] > 1200 and match['game_mode'] == 22]
        # remove duplicates
        self.data = list({match['match_id']: match for match in self.data}.values())
    def return_matchids(self):
        return [match['match_id'] for match in self.data]


def get_recent_pro_matches(hero_id):
    response = requests.get(f"https://api.opendota.com/api/heroes/{hero_id}/matches")
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        return None
    

def get_hero_database():
    try:
        herodatabase = open("herodatabase.json", "r")
        herodatabase = json.loads(herodatabase.read())
    except:
        response = requests.get('https://api.opendota.com/api/heroes')
        if response.status_code == 200:
            heroes = response.json()
        herodatabase = open("herodatabase.json", "w")
        herodatabase.write(json.dumps(heroes))
        herodatabase.close()
        herodatabase = heroes
    return herodatabase


herodatabase = get_hero_database()

# new way to generate matches
counter = Match_numbers()    
counter.get_public_matches()
counter.get_more()
# print hello world 10 times using lambda
list(map(lambda x: counter.get_more(), range(10)))



counter.vet_data()
counter.len()
zgeneratedmatches = counter.return_matchids()

# last 200
generatedmatches = zgeneratedmatches[-1000:]
match =  mid_matchup(generatedmatches[-200:][1])
database.append(Match(*match.retunformatch()).to_dict())
open("database.json", "w").write(json.dumps(database))
match.retunformatch()



# open locally store databse.json

temp_database = open("database.json", "r")
temp_database = json.loads(temp_database.read())
loopcounter = 0 
for matchID in generatedmatches:
    loopcounter +=1
    print(f"loop: {loopcounter}")
    if matchID not in [x['matchid'] for x in temp_database]:
        try:
            match = mid_matchup(matchID)
            if (len(match.mid_players)>2):
                print(f"Match ID {matchID} rejected code1, more than 2 players in mid lane")
                continue
            temp_database.append(Match(*match.retunformatch()).to_dict())
            open("tempfile.tmp", "a").write(","+str(json.dumps(Match(*match.retunformatch()).to_dict())))
            print(f"Match ID {matchID} added to database.")
        except:
            print(f"Match ID {matchID} rejected code2, not parsed")
            continue
    else:
        print("already parsed")

open("database.json", "w").write(json.dumps(temp_database))

# how to use
# generate the databse using the action.py loose code













import pandas as pd
import numpy as np
import json
from collections import Counter



database = json.loads(open("database.json", "r").read())
df = pd.read_json('database.json')


# Count occurrences in both columns
winner_counts = df['winner'].value_counts()
looser_counts = df['looser'].value_counts()

# Add the counts together
hero_counts = winner_counts.add(looser_counts, fill_value=0)

# The heroes with the highest counts are the most played
most_played_heroes = hero_counts.sort_values(ascending=False)



# add winrate column to most_played_heroes
winrate = []
for hero in most_played_heroes.index:
    findall = df[(df['winner'] == hero) | (df['looser'] == hero)]
    winrate.append(len(findall[findall['winner'] == hero]) / len(findall) *100)


most_played_heroes = pd.DataFrame(most_played_heroes)
most_played_heroes['winrate'] = winrate
# export csv
most_played_heroes.to_csv("most_played_heroes.csv")













