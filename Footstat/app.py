import streamlit as st
from supabase import create_client, Client
import pandas as pd

@st.cache_resource
def init_connection() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

st.title("Footstat")
options_goals=["1+","2+","3+","4+"]
filter_button = st.selectbox("Goals", options=options_goals, index=2)

options_leagues=["Championship England", "League 1", "League 2", "National League"]
filter_league_button = st.selectbox("Leagues", options=options_leagues)

def filter_options_table(goals,league):
    if filter_button == goals:
        goals_selection = int(goals.replace("+" , ""))
        or_filter = f"hometeamscorefull.gte.{goals_selection},awayteamscorefull.gte.{goals_selection}"
        
        response = supabase.table("match").select(
            "League, home_team:team!hometeamid_fk(name), hometeamscorehalf, hometeamscorefull, away_team:team!awayteamid_fk(name), awayteamscorehalf, awayteamscorefull, date"
        ).or_(or_filter).eq('League',league).order("date",desc=True).execute()

        df = pd.json_normalize(response.data)

        df = df[["League", "home_team.name", "hometeamscorehalf", "hometeamscorefull", "away_team.name", "awayteamscorehalf", "awayteamscorefull", "date"]]
        
        df.columns = ["League" , "Home", "HT-H", "HT-F", "Away", "AW-H", "AW-F", "Date"]

        return df

def get_max_goals_df():

    response = supabase.table("match").select("League, home_team:team!hometeamid_fk(name), hometeamscorefull").eq

result_table = filter_options_table(filter_button,filter_league_button)

column_order = ("Home", "HT-H", "HT-F", "Away", "AW-H", "AW-F", "Date")

st.dataframe(result_table,
             width="content", 
             hide_index=True,
             column_order=column_order)

