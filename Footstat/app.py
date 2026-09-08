import streamlit as st
from supabase import create_client, Client
import pandas as pd
import altair as alt

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
        
        df.columns = ["League" , "Home Team", "Home Half Score", "Home Final Score", "Away Team", "Away Half Score", "Away Final Score", "Date"]

        return df

# def max_goals_df

result_table = filter_options_table(filter_button,filter_league_button)

st.dataframe(result_table,
             use_container_width=False, 
             hide_index=True,)

chart = (
    alt.Chart(result_table)
    .mark_bar()
    .encode(
        alt.X("Nucleotide:O"),
        alt.Y("Similarities"),
        alt.Color("Nucleotide:O"),
        alt.Tooltip(["Nucleotide", "Similarities"]),
    )
    .interactive()
)
st.altair_chart(chart)
