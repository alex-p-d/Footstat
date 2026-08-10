import requests
import json

uri = 'https://api.football-data.org/v4/matches'
headers = { 'X-Auth-Token': 'UR_TOKEN' }

response = requests.get(uri, headers=headers)
for match in response.json()['matches']:
  print(match)