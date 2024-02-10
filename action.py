import time
import pandas as pd
import numpy as np
import json
from collections import Counter
import json
import requests


def wfile(var):
    writevartofile = open("tempvar.json", "w")
    writevartofile.write(json.dumps(var))
    writevartofile.close()
    print("written to tempvar.json")


class Match:
    def __init__(self, matchid,playerrank, winner, looser, winner_efficiency, looser_efficiency, didWinnerWin):
        self.matchid = matchid
        self.playerrank = playerrank
        self.winner = winner
        self.looser = looser
        self.winner_efficiency = winner_efficiency
        self.looser_efficiency = looser_efficiency
        self.didWinnerWin = didWinnerWin
    def to_dict(self):
        return {
            'matchid': self.matchid,
            'playerrank': self.playerrank,
            'winner': self.winner,
            'looser': self.looser,
            'winner_efficiency': self.winner_efficiency,
            'looser_efficiency': self.looser_efficiency,
            'didWinnerWin': self.didWinnerWin
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
        self.didWinnerWin = None
        if self.isParsed:
            self.mid_lane_matchup()
            self.get_winner()
            self.get_matchrank()   
            self.get_didWinnerWin()
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
    def get_didWinnerWin(self):
        if self.winner:
            if self.winner["player_slot"]<128:
                self.playerside = "radiant"
            else:
                self.playerside = "dire"
            if (self.match_data["radiant_win"]):
                winner = "radiant"
            else:
                winner = "dire"
            self.didWinnerWin = (self.playerside == winner)
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
        return self.matchid, self.matchrank, self.winner['hero_id'], self.loser['hero_id'], self.winner['lane_efficiency_pct'], self.loser['lane_efficiency_pct'], self.didWinnerWin
    def get_match_data(self, match_id):
        response = requests.get(f"https://api.opendota.com/api/matches/{match_id}")
        if response.status_code == 200:
            time.sleep(0.3)# to avoid api limit
            #if jsonload contain version returns a keyerror 
            try:
                json.loads(response.text)["version"]
                self.isParsed = True
            except KeyError:
                self.isParsed = False
            return json.loads(response.text)
        elif response.status_code == 429:
            print("daily api limit exceeded")
            print(response.text)
            time.sleep(30)
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
        if response.status_code == 200:
            data = response.json()
        else:
            print(f"failed to fetch public matches, status code: {response.status_code}")
            print(response.text)
            return None
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

# new way to generate matches
def get_data_matches()->Match_numbers:
    """
    Returns a single Match_numbers object 
    with around 2000 cleaned immortal matches 
    from around yesterday 
    in the .data property
    use .return_matchids() to grab only the matchids
    """
    # init counter to get current mach id's
    counter = Match_numbers()    
    counter.get_public_matches()
    recentMatchNumber = counter.data[0]["match_id"]
    # skip the equivalent of 20 get_more() calls
    startfrom = recentMatchNumber - 100000 * 20
    # reinit counter
    counter = Match_numbers()    
    counter.get_public_matches(startfrom)
    [counter.get_more() for _ in range(20)]
    counter.vet_data()
    f"storing {counter.len()} matches between {counter.data[0]["match_id"]} to {counter.data[-1]["match_id"]}"
    return counter


def populate_database(machIDList):
    # assign full db to a temp variable
    temp_database = open("database.json", "r")
    temp_database = json.loads(temp_database.read())
    for loopcounter, matchID in enumerate(machIDList):
        print(f"loop: {loopcounter}",end=" -- ")
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
            print(f"{matchID} already added")
    open("database.json", "w").write(json.dumps(temp_database))



def generate_summary():
    """
    this generate a summary.json file that will be used by pythonweb.py to generate html component on server start
            matchid  playerrank  winner  looser  winner_efficiency  looser_efficiency  didWinnerWin
    0    7576198207          75     114     106                108                 61           NaN
    1    7576197207          75      74      22                 77                 76           NaN
    2    7576192119          75      47      59                 98                 64           NaN
    3    7576177017          75     126     137                 77                 72           NaN
    4    7576170519          75      35     120                 78                 71           NaN
    ..          ...         ...     ...     ...                ...                ...           ...
    953  7574420705          75      59      46                 81                 68           0.0
    954  7574417718          75      15      43                 94                 93           0.0
    955  7574416907          75      25      76                 98                 69           0.0
    956  7574416016          75      62      49                102                 77           1.0
    957  7574415200          75     120     106                 82                 64           1.0
    """
    df = pd.read_json('database.json')
    # Combine 'winner' and 'looser' columns into a single column 'player'
    df_players = pd.concat([df['winner'], df['looser']], ignore_index=True)
    # Count the number of matches each player has played
    matches_played = df_players.value_counts().rename('matches_played')
    # Count the number of matches each player has won
    wins = df['winner'].value_counts()
    # Calculate the lane win rate for each player
    laneWinrate = (wins / matches_played).rename('laneWinrate')
    #---------------------- calculating using schema v2
    # Exclude rows where 'didWinnerWin' is NaN
    ddww = df[df['didWinnerWin'].notna()]
    ddww_players = pd.concat([ddww['winner'], ddww['looser']], ignore_index=True)
    matches_playedv2 = ddww_players.value_counts().rename('matches_played')
    # Calculate the game win rate for each player
    winsv2 = ddww[ddww['didWinnerWin'] == True]['winner'].value_counts()
    winsv2inversecalc = ddww[ddww['didWinnerWin'] == False]['looser'].value_counts()
    # add winsv2 and winsv2inversecalc
    winsv2 = winsv2.add(winsv2inversecalc, fill_value=0)
    gameWinrate = (winsv2 / matches_playedv2).rename('gameWinrate')
    #---------------------- calculating using schema v2
    # Combine 'matches_played', 'laneWinrate' and 'gameWinrate' into a single dataframe
    df_summary = pd.concat([matches_played, laneWinrate, gameWinrate], axis=1).reset_index().rename(columns={'index': 'playerID'})
    # Fill NaN values with 0 (players who have never won a match)
    df_summary['laneWinrate'].fillna(0, inplace=True)
    df_summary['gameWinrate'].fillna(0, inplace=True)
    # write json to a file 
    df_summary.to_json("summary.json", orient="records")


def chunk_list(input_list, chunk_size):
    """Yield successive n-sized chunks from input_list."""
    for i in range(0, len(input_list), chunk_size):
        yield input_list[i:i + chunk_size]


# ---------------------------------------




# required by pythonweb.py
get_hero_database()

# required by pythonweb.py
generate_summary()

# genera ID's
counter = get_data_matches()#20 api calls
counter.get_more()


generatedmatches = counter.return_matchids()

# manual single block
populate_database(generatedmatches[0:100])

# chunking list in to blocks of 10
for chunkcounter, chunk in enumerate(chunk_list(generatedmatches[0:100], 10)):
    print(f"chunkcounter: {chunkcounter}")
    populate_database(chunk)
    generate_summary()


database = open("database.json", "r")    
database = json.loads(database.read())

# test for generatedmatches in database[x]["matchid"]
for matchid in generatedmatches[2000:3000]:
    if matchid in [x["matchid"] for x in database]:
        print(f"{matchid} already added")
    else:
        print(f"{matchid} not in database")

