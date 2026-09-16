import streamlit as st
from supabase import create_client, Client
import pandas as pd

@st.cache_resource
def init_connection() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

st.markdown("<h1 style='text-align: center; color: black;'>Footstat - football statistics</h1>", unsafe_allow_html=True)
st.divider()
options_goals=["1+","2+","3+","4+"]
filter_button = st.selectbox("Голове", options=options_goals, index=2)
options_leagues=['Championship England', 'League 1', 'League 2', 'National League',
                 'Spain - LaLiga','Spain - LaLiga 2','Germany - Bundesliga',
                 'France - Ligue 1','Belgian Pro League','Netherlands - Eredivisie',
                 'Italian - Serie A','Portugal - Primeira Liga','Austrian Bundesliga',
                 'Brazilian - Serie A','Mexico - Liga MX','Argentina - Liga Profesional',
                 'Scottish Premiership','Saudi Pro League','USA - Major League Soccer',
                 'Japanese J.League','Turkish - Super Lig']

########

def get_highest_scoring_teams(league):

    top_scoring_teams_response = supabase.table("team_totals").select(
    "name", "League", "total_score_home", "total_score_away").execute()
    
    df_top_scoring_teams = pd.json_normalize(top_scoring_teams_response.data)

    df_only_one_league = df_top_scoring_teams[df_top_scoring_teams['League'] == league]

    most_goals_team_home = df_only_one_league.sort_values(by=['total_score_home'], ascending=[False])
    most_goals_team_away = df_only_one_league.sort_values(by=['total_score_away'], ascending=[False])

    most_goals_team_home_df = most_goals_team_home[['name','total_score_home']]
    most_goals_team_home_df = most_goals_team_home_df.rename(columns={'name' : 'Като домакини', 'total_score_home' : 'Голове Домакини'}).reset_index(drop=True)
    most_goals_team_away_df = most_goals_team_away[['name','total_score_away']]
    most_goals_team_away_df = most_goals_team_away_df.rename(columns={'name' : 'Като гости', 'total_score_away' : 'Голове Гости'}).reset_index(drop=True)
    highest_goals_teams = pd.concat([most_goals_team_home_df,most_goals_team_away_df],axis=1)

    return highest_goals_teams

########
filter_league_button = st.selectbox("Лига", options=options_leagues)

def filter_options_table(goals,league):
    if filter_button == goals:
        goals_selection = int(goals.replace("+" , ""))
        or_filter = f"hometeamscorefull.gte.{goals_selection},awayteamscorefull.gte.{goals_selection}"
        
        response = supabase.table("match").select(
            "League, home_team:team!hometeamid_fk(name), hometeamscorehalf, hometeamscorefull, away_team:team!awayteamid_fk(name), awayteamscorehalf, awayteamscorefull, date"
        ).or_(or_filter).eq('League',league).order("date",desc=True).execute()

        df = pd.json_normalize(response.data)

        df = df[["League", "home_team.name", "hometeamscorehalf", "hometeamscorefull", "away_team.name", "awayteamscorehalf", "awayteamscorefull", "date"]]
        
        df.columns = ['Лига', 'Домакини', 'Полувреме-Д', 'Краен-Д', 'Гости', 'Полувреме-Г', 'Краен-Г', 'Дата']

        return df

result_table = filter_options_table(filter_button,filter_league_button)

column_order = ('Домакини', 'Полувреме-Д', 'Краен-Д', 'Гости', 'Полувреме-Г', 'Краен-Г', 'Дата')

st.divider()

st.markdown("<h5 style='text-align: center; color: black;'>Мачове</h5>", unsafe_allow_html=True)

st.dataframe(result_table,
             width="content", 
             hide_index=True,
             column_order=column_order)

highest_goal_teams = get_highest_scoring_teams(filter_league_button)

st.divider()
st.markdown("<h5 style='text-align: center; color: black;'>Отбори с най-много голове</h5>", unsafe_allow_html=True)
# st.write("Отбори с най-много голове")

st.dataframe(highest_goal_teams,
             width="stretch", 
             hide_index=True,
             )

