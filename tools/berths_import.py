import json

from app import db
from models import Berth

LOCATIONS_FILE = "locations.json"  # JSON file containing berth locations

with open(LOCATIONS_FILE) as file:
    data = file.read()
    json = json.loads(data)

    for td in json:
        for berth_name in json[td]:
            berth = Berth(td, berth_name, json[td][berth_name]["lat"], json[td][berth_name]["lon"])
            print(repr(berth))
            db.session.add(berth)

    db.session.commit()

