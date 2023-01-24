import time

from app import db
from models import TrainDescription, Berth, BerthRecord

import json
import stomp
from datetime import datetime as dt


def process_td_message(message):
    if "CT_MSG" in message:
        data = message["CT_MSG"]
        if data["area_id"] not in ["EA", "TW", "AL", "MO"]:
            return
        print(data["area_id"], data["time"])
        print(dt.utcfromtimestamp(int(data['time']) / 1000))
        print()

    if "CA_MSG" in message:
        data = message["CA_MSG"]

        # Testing
        if data["area_id"] not in ["EA", "TW", "AL", "MO"]:
            return

        # Filter unwanted descriptions
        if '*' in data['descr']:
            return

        # Find berths
        from_berth = find_berth(data["area_id"], data["from"])
        to_berth = find_berth(data["area_id"], data["to"])

        # If neither berths exist in database
        if from_berth is None and to_berth is None:
            return

        print(data["area_id"], data["descr"], data["from"], data["to"])

        timestamp = dt.utcfromtimestamp(int(data['time']) / 1000)  # timestamp of message from train describer

        # Retrieve train object
        train = get_train(data["area_id"], data["descr"])

        if train is None:
            print("Train object doesn't exist, create one")
            # Train object doesn't exist, create one
            train = TrainDescription(data["area_id"], data["descr"], None, timestamp)

            if to_berth:
                train.active = True
                # TODO: Add check for any trains already occupying this berth
                train.current_berth = to_berth
            else:
                train.active = False
                # If to berth doesn't exist, from berth must exist here
                train.current_berth = from_berth

            # Add train to database
            db.session.add(train)
            db.session.commit()

        else:
            # Train object already exists
            print("Train object already exists")

            if to_berth:
                print("To berth found, train active")

                # Discard message if to berth already matches (likely duplicate message)
                if train.current_berth.id == to_berth.id:
                    print("Discarding message - berth already matches")
                    return

                train.active = True
                # TODO: Add check for any trains already occupying this berth
                train.current_berth = to_berth
            else:
                print("To berth not found, train inactive")
                train.active = False
                # If to berth doesn't exist, from berth must exist here
                train.current_berth = from_berth

        # Check from berth
        if from_berth:
            print("From berth found")

            # Create berth history record
            history_record = BerthRecord(train.id, from_berth.id, timestamp)
            db.session.add(history_record)
            db.session.commit()

            # If berth borders another train describer
            if from_berth.borders_describer:
                print("Borders describer", from_berth.borders_describer)
                train.describer = from_berth.borders_describer  # Update for next train describer
                berth = find_berth(from_berth.borders_describer, data["to"])
                if berth:
                    print("Found berth from next TD, train active", berth)
                    train.active = True
                    # TODO: Add check for any trains already occupying this berth
                    train.current_berth_id = berth.id
                else:
                    print("Could not find berth from next TD, train inactive", data["to"])
                    train.active = False

        db.session.commit()
        print(train)
        print()


def get_train(area, description):
    query = db.session.query(TrainDescription).filter(
        TrainDescription.describer == area,
        TrainDescription.description == description,
        TrainDescription.cancelled == 0)

    return query.first()


def find_berth(area, berth):
    query = db.session.query(Berth).filter(Berth.describer == area, Berth.berth == berth)
    return query.first()


def process_movement_message(message):
    pass


class Listener(stomp.ConnectionListener):
    # Exponential backoff variables for reconnects
    reconnect_time = 15
    current_wait_time = reconnect_time

    def __init__(self, conn, connect_method):
        self.conn = conn
        self.connect_method = connect_method

    def on_disconnected(self):
        print(f'Disconnected, waiting {self.current_wait_time} seconds before reconnect')
        time.sleep(self.current_wait_time)
        self.current_wait_time *= 2  # Increase wait time for next reconnect

        self.connect_method()

    def on_error(self, frame):
        message = frame.body
        print("Error:", message)

    def on_message(self, frame):
        self.current_wait_time = self.reconnect_time  # Reset wait time

        data = json.loads(frame.body)
        headers = frame.headers

        # TD Messages
        if headers["destination"] == "/topic/TD_ALL_SIG_AREA":
            [process_td_message(message) for message in data]

        # Train Movement Message
        elif headers["destination"] == "/topic/TRAIN_MVT_ALL_TOC":
            [process_movement_message(message) for message in data]


class NROD:
    def __init__(self, host, port, username, password, subscription_name):
        self._username = username
        self._password = password
        self._subscription_name = subscription_name

        self.conn = stomp.Connection([(host, port)], keepalive=True, heartbeats=(10000, 5000))
        self.conn.set_listener('', Listener(self.conn, self.connect_and_subscribe))
        self.connect_and_subscribe()

    def connect_and_subscribe(self):
        self.conn.connect(**{
            "username": self._username,
            "passcode": self._password,
            "wait": True,
            "client-id": self._username + '1',
        })
        self.conn.subscribe(**{
            "destination": "/topic/TD_ALL_SIG_AREA",
            "id": 1,
            "ack": "auto",
            "activemq.subscriptionName": self._subscription_name + "-td",
        })
        self.conn.subscribe(**{
            "destination": "/topic/TRAIN_MVT_ALL_TOC",
            "id": 2,
            "ack": "auto",
            "activemq.subscriptionName": self._subscription_name + "-mvt",
        })

        print("Connected and subscribed")
