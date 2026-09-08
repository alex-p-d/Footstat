import requests
import json

url = "https://worldcup26.ir/get/soccer/eng.2/fixtures"

response = requests.get(url)
data = response.json()

print(json.dumps(data, indent=4))