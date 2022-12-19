from app import db
from TrainDescription import TrainDescription

import json
import stomp
from datetime import datetime as dt

train_descriptions = {}


def process_td_message(message):
    if "CA_MSG" in message:
        data = message["CA_MSG"]

        # Testing
        if data["area_id"] not in ["EA", "EB"]:
            return

        # Filter unwanted descriptions
        if '*' in data['descr']:
            return

        from_berth = data["from"]
        to_berth = data["to"]

        if data['area_id'] + data['descr'] in train_descriptions:
            # Train already known
            # First check if train is about to step into a different area
            train_descriptions[data['area_id'] + data['descr']].change_berth(to_berth, None)
        else:
            # New train description
            train_descriptions[data['area_id'] + data['descr']] = TrainDescription(data['area_id'], data['descr'], to_berth, None, from_berth)

        print(train_descriptions)


def process_movement_message(message):
    pass

class Listener(stomp.ConnectionListener):
    def __init__(self, conn, connect_method):
        self.conn = conn
        self.connect_method = connect_method

    def on_disconnected(self):
        print('Disconnected')
        self.connect_method()

    def on_error(self, frame):
        message = frame.body
        print("Error:", message)

    def on_message(self, frame):
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
