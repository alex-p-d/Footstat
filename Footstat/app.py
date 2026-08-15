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
filter_button = st.selectbox("Goals", options=[1,2,3,4], index=2)

def filter_options(goals):
    if filter_button == goals:

        or_filter = f"hometeamscorefull.gt.{goals},awayteamscorefull.gt.{goals}"
        response = supabase.table("matchtest").select("home_team:teamtest!hometeamid_fk(name), hometeamscorehalf, hometeamscorefull, away_team:teamtest!awayteamid_fk(name), awayteamscorehalf, awayteamscorefull").gt("hometeamscorefull", goals).or_(or_filter).execute()

        df = pd.json_normalize(response.data)

        df = df[["home_team.name","hometeamscorehalf","hometeamscorefull","away_team.name","awayteamscorehalf","awayteamscorefull"]]
        df.columns = ["Home Team", "Home Half Time Score", "Home Final Score", "Away Team", "Away Half Time Score", "Away Final Score"]

        return df

result_table = filter_options(filter_button)

st.dataframe(result_table)