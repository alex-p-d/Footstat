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
league_list = ['eng.2','eng.3','eng.4','eng.5','esp.1','esp.2','ger.1',
               'fra.1','bel.1','ned.1','ita.1','por.1','aut.1','bra.1',
               'mex.1','arg.1','sco.1','ksa.1','usa.1','jpn.1','tur.1']

league_dict = {'eng.2':'Championship England','eng.3':'League 1',
               'eng.4':'League 2','eng.5':'National League',
               'esp.1':'Spain - LaLiga','esp.2':'Spain - LaLiga 2','ger.1':'Germany - Bundesliga',
               'fra.1':'France - Ligue 1','bel.1':'Belgian Pro League',
               'ned.1':'Netherlands - Eredivisie','ita.1':'Italian - Serie A',
               'por.1':'Portugal - Primeira Liga','aut.1':'Austrian Bundesliga',
               'bra.1':'Brazilian - Serie A', 'mex.1':'Mexico - Liga MX',
               'arg.1':'Argentina - Liga Profesional','sco.1':'Scottish Premiership',
               'ksa.1':'Saudi Pro League','usa.1':'USA - Major League Soccer',
               'jpn.1':'Japanese J.League','tur.1':'Turkish - Super Lig'
               }

def set_league_name(league, league_dict):
    return league_dict.get(league)
   

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
            'League' : set_league_name(league, league_dict),
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
home_teams = final_df[['Home Team ID', 'Home Team']].rename(
    columns={'Home Team ID': 'id', 'Home Team': 'name'})

away_teams = final_df[['Away Team ID', 'Away Team']].rename(
    columns={'Away Team ID': 'id', 'Away Team': 'name'})

teams_df = pd.concat([home_teams, away_teams], ignore_index=True)

teams_df = teams_df.drop_duplicates(subset=['id'], keep='first')
teams_list = teams_df.to_dict(orient='records')

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

duplicate_ids = final_df[
    final_df.duplicated(subset=['ID'], keep=False)
].sort_values('ID')

print(duplicate_ids[
    ['ID', 'League', 'Date', 'Home Team', 'Away Team']
].to_string(index=False))

print(f"Found {len(matches_list)} matches ready for insert.")

score_cols = ['hometeamscorehalf', 'hometeamscorefull', 'awayteamscorehalf', 'awayteamscorefull']
for match in matches_list:
    for col in score_cols:
        if match.get(col) is not None:
            match[col] = int(match[col])

print("UPserting teams...")
response = (
    supabase.table("team")
    .upsert(teams_list)
    .execute()
)

print("UPserting matches...")
response = (
    supabase.table("match")
    .upsert(matches_list)
    .execute()
)

print("DONE")
