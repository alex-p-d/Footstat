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
options=["1+","2+","3+","4+"]
filter_button = st.selectbox("Goals", options=options, index=2)

def filter_options(goals):
    if filter_button == goals:
        goals_selection = int(goals.replace("+" , ""))
        or_filter = f"hometeamscorefull.gte.{goals_selection},awayteamscorefull.gte.{goals_selection}"
        response = supabase.table("matchtest").select("home_team:teamtest!hometeamid_fk(name), hometeamscorehalf, hometeamscorefull, away_team:teamtest!awayteamid_fk(name), awayteamscorehalf, awayteamscorefull, date").or_(or_filter).order("date",desc=True).execute()

        df = pd.json_normalize(response.data)

        df = df[["home_team.name","hometeamscorehalf","hometeamscorefull","away_team.name","awayteamscorehalf","awayteamscorefull", "date"]]
        df.columns = ["Home Team", "Home Half Time Score", "Home Final Score", "Away Team", "Away Half Time Score", "Away Final Score", "Date"]

        return df

result_table = filter_options(filter_button)

st.dataframe(result_table)

