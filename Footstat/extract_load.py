import requests
import json
import os
from dotenv import load_dotenv
import pandas as pd
from supabase import create_client, Client

###############
load_dotenv()
TOKEN = os.getenv("API_KEY")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
supabase: Client = create_client(SUPABASE_URL,SUPABASE_KEY)
uri = 'https://api.football-data.org/v4/competitions/PL/matches?season=2026'
headers = { 'X-Auth-Token': TOKEN }
###############

response = requests.get(uri, headers=headers)

matches_data = response.json().get('matches', [])
df = pd.json_normalize(matches_data)

# list of dictionaries of teams to insert into postgres
team_columns = ['homeTeam.id' , 'homeTeam.shortName', 'homeTeam.crest']
teams_list = (df[team_columns]
            .copy()
            .drop_duplicates()
            .rename(columns={'homeTeam.id':'id',
                             'homeTeam.shortName':'name',
                             'homeTeam.crest':'logo'})
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

matches_list = (df[matches_columns]
              .copy()
              .rename(columns={'id':'id',
                               'utcDate':'date',
                               'status':'status',
                               'group':'group',
                               'homeTeam.id':'hometeamid',
                               'awayTeam.id':'awayteamid',
                               'score.halfTime.home':'hometeamscorehalf',
                               'score.fullTime.home':'hometeamscorefull',
                               'score.halfTime.away':'awayteamscorehalf',
                               'score.fullTime.away':'awayteamscorefull',})
                               .to_dict(orient='records'))

# insert into postgres
# incoming premier league season
print(matches_list)
response = (
    supabase.table("team")
    .upsert(teams_list)
    .execute()
)

response = (
    supabase.table("match")
    .upsert(matches_list)
    .execute()
)

# previous season just using for testing currently
# response = (
#     supabase.table("teamtest")
#     .upsert(teams_list)
#     .execute()
# )

# response = (
#     supabase.table("matchtest")
#     .upsert(matches_list)
#     .execute()
# )

