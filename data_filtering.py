import json
from pprint import pprint

with open("vo_showings.json", "r", encoding="utf8") as f:
    data = json.load(f)

pprint(data[0])
