import requests
import json
import os
from dotenv import load_dotenv
import pandas as pd

# Setting display options for terminal
pd.set_option('display.max_columns', None)

###############
load_dotenv()
TOKEN=os.getenv("API_KEY")
uri = 'https://api.football-data.org/v4/competitions/PL/matches'
headers = { 'X-Auth-Token': TOKEN }
###############

response = requests.get(uri, headers=headers)

matches_data = response.json().get('matches', [])
df = pd.json_normalize(matches_data)

# list of dictionaries of teams to insert into postgres
team_columns = ['homeTeam.id' , 'homeTeam.shortName', 'homeTeam.crest']
teams_dict = (df[team_columns]
            .copy()
            .drop_duplicates()
            .rename(columns={'homeTeam.id':'ID',
                             'homeTeam.shortName':'Name',
                             'homeTeam.crest':'Logo'})
            .to_dict(orient='records'))

# list of dictionaries of matches to insert into postgres
matches_columns = ['id',
                   'utcDate',
                   'status',
                   'group',
                   'homeTeam.id',
                   'awayTeam.id',
                   'score.halfTime.home',
                   'score.fullTime.home',
                   'score.halfTime.away',
                   'score.fullTime.away']

matches_dict = (df[matches_columns]
              .copy()
              .rename(columns={'id':'ID',
                               'utcDate':'Date',
                               'status':'Status',
                               'group':'Group',
                               'homeTeam.id':'Hometeam',
                               'awayTeam.id':'Awayteam',
                               'score.halfTime.home':'HometeamScoreHalf',
                               'score.fullTime.home':'HometeamScoreFull',
                               'score.halfTime.away':'AwayteamScoreHalf',
                               'score.fullTime.away':'AwayeamScoreFull',})
                               .to_dict(orient='records'))

print(matches_dict)


