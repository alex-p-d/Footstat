import requests
import json
import os
from dotenv import load_dotenv
import pandas as pd
from supabase import create_client, Client
import numpy as np

# ==========================================
# 1. SETUP ENVIRONMENT & SUPABASE
# ==========================================
load_dotenv()
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.expand_frame_repr', False)

# ==========================================
# 2. YOUR EXACT DATA FETCHING LOGIC
# ==========================================
league_list = ['eng.2','eng.3','eng.4','eng.5']

def set_league_name(league):
    name = ''
    if league == 'eng.2':
        name = 'Championship England'
    elif league == 'eng.3':
        name = 'League 1'
    elif league == 'eng.4':
        name = 'League 2'
    elif league == 'eng.5':
        name = 'National League'
    return name

clean_matches_list = list()

for league in league_list:

    url = f"https://worldcup26.ir/get/soccer/{league}/fixtures?status=all"

    headers = {
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    df = pd.json_normalize(data['events'],record_path='competitions')

    for i in df.itertuples():

        home_ht_goals = 0
        away_ht_goals = 0
        match_id = i.id
        match_date = i.date 
        
        homeTeamID = i.competitors[0]['team']['id']
        homeTeamName = i.competitors[0]['team']['displayName']
        homeTeamScore = i.competitors[0].get('score')
        awayTeamID = i.competitors[1]['team']['id']
        awayTeamName = i.competitors[1]['team']['displayName']
        awayTeamScore = i.competitors[1].get('score')

        for j in i.details:
            if j.get('type', {}).get('text') == 'Goal':
                if j['clock']['value'] <= 2700:
                    if j['team']['id'] == homeTeamID:
                        home_ht_goals += 1
                    elif j['team']['id'] == awayTeamID:
                        away_ht_goals += 1
                                
        clean_matches_list.append(
            {
            'League' : set_league_name(league),
            'ID' : match_id,
            'Date' : match_date,
            'Home Team ID' : homeTeamID,
            'Home Team' : homeTeamName,
            'Home Team HF Score' : home_ht_goals,
            'Home Team Final Score' : homeTeamScore,
            'Away Team ID' : awayTeamID,
            'Away Team' : awayTeamName,
            'Away Team HF Score' : away_ht_goals,
            'Away Team Final Score' : awayTeamScore
            }
        ) 

final_df = pd.DataFrame(clean_matches_list)

# list of dictionaries of teams to insert into postgres
team_columns = ['Home Team ID', 'Home Team']
teams_list = (final_df[team_columns]
            .copy()
            .drop_duplicates()
            .rename(columns={'Home Team ID':'id',
                             'Home Team':'name'})
            .to_dict(orient='records'))

# list of dictionaries of matches to insert into postgres
matches_columns = ['ID',
                   'Date',
                   'League',
                   'Home Team ID',
                   'Away Team ID',
                   'Home Team HF Score',
                   'Home Team Final Score',
                   'Away Team HF Score',
                   'Away Team Final Score']

matches_list = (final_df[matches_columns]
              .copy()
              .rename(columns={'ID':'id',
                               'Date':'date',
                               'League':'League',
                               'Home Team ID':'hometeamid',
                               'Away Team ID':'awayteamid',
                               'Home Team HF Score':'hometeamscorehalf',
                               'Home Team Final Score':'hometeamscorefull',
                               'Away Team HF Score':'awayteamscorehalf',
                               'Away Team Final Score':'awayteamscorefull'})
                               .replace({np.nan: None})
                               .to_dict(orient='records'))


print(f"Found {len(matches_list)} matches ready for insert.")

score_cols = ['hometeamscorehalf', 'hometeamscorefull', 'awayteamscorehalf', 'awayteamscorefull']
for match in matches_list:
    for col in score_cols:
        if match.get(col) is not None:
            match[col] = int(match[col])

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