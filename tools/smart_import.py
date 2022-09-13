import json

from app import db
from models import Berth, Smart

SMART_FILE = "SMART.json"  # JSON file containing SMART data
TRAIN_DESCRIBERS = ["TW", "AL", "T1", "EA", "EB", "M0"]  # List of train describers which will be imported


def check_berth(describer, berth_name):
    # Check if berth exists
    berth = Berth.query.filter_by(describer=describer, berth=berth_name).first()

    # Create new berth if doesn't exist
    if not berth:
        berth = Berth(describer, berth_name)
        db.session.add(berth)


with open(SMART_FILE) as file:
    data = file.read()
    json = json.loads(data)

    # If berth data exists
    if "BERTHDATA" in json:

        # Iterate through each berth step object
        for data in json["BERTHDATA"]:
            step_type = data["STEPTYPE"]
            from_berth = None if data["FROMBERTH"] == '' else data["FROMBERTH"]
            to_berth = None if data["TOBERTH"] == '' else data["TOBERTH"]
            stanox = data["STANOX"]
            event = data["EVENT"]
            platform = None if data["PLATFORM"] == '' else data["PLATFORM"]
            to_line = None if data["TOLINE"] == '' else data["TOLINE"]
            berth_offset = data["BERTHOFFSET"]
            route = None if data["ROUTE"] == '' else data["ROUTE"]
            from_line = None if data["FROMLINE"] == '' else data["FROMLINE"]
            td = data["TD"]
            comment = None if data["COMMENT"] == '' else data["COMMENT"]
            stanme = None if data["STANME"] == '' else data["STANME"]

            # Only import data for the train describers specified
            if td in TRAIN_DESCRIBERS:
                if from_berth is not None:
                    check_berth(td, from_berth)

                if to_berth is not None:
                    check_berth(td, to_berth)

                db.session.commit()

                smart = Smart(step_type=step_type, from_berth=from_berth, to_berth=to_berth, stanox=stanox, event=event,
                              platform=platform, to_line=to_line, berth_offset=berth_offset, route=route,
                              from_line=from_line, td=td, comment=comment, stanme=stanme)
                print(smart)

                db.session.add(smart)

        db.session.commit()

