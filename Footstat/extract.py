import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()

TOKEN=os.getenv("API_KEY")

uri = 'https://api.football-data.org/v4/matches'
headers = { 'X-Auth-Token': TOKEN }

response = requests.get(uri, headers=headers)
for match in response.json()['matches']:
  print(match)