import streamlit as st
from supabase import create_client, Client

@st.cache_resource
def init_connection() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

    # response = supabase.table("match").select("*").execute()
    # return response.data

options = ["1+","2+","3+","4+"]

st.title("Footstat")
filter_button = st.menu_button("Goals", options=options)

if filter_button == 1:
    response = supabase.table("matchtest").select("*").gt("hometeamscorefull", 3).gt("awayteamscorehalf",3).execute()
    st.dataframe(response.data)

