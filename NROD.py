from app import db
from models import TrainDescription, Berth, Trust

import json
import stomp
from datetime import datetime as dt


def process_td_message(message):
    if "CA_MSG" in message:
        data = message["CA_MSG"]

        # Filter unwanted descriptions
        if '*' in data['descr']:
            return

        from_berth = Berth.query.filter_by(describer=data["area_id"], berth=data["from"]).first()
        to_berth = Berth.query.filter_by(describer=data["area_id"], berth=data["to"]).first()

        if from_berth and to_berth:
            timestamp = dt.utcfromtimestamp(int(data['time']) / 1000)  # timestamp of message from train describer

            # Add database entry
            description = TrainDescription(data['area_id'], data['descr'], timestamp, from_berth.id, to_berth.id)
            db.session.add(description)
            db.session.commit()

            # Debug
            if from_berth.latitude and from_berth.longitude and to_berth.latitude and to_berth.longitude:
                print(f"Area {data['area_id']}: Train {data['descr']} going from "
                      f"{from_berth.berth} ({from_berth.latitude}, {from_berth.longitude}) "
                      f"to {to_berth.berth} ({to_berth.latitude}, {to_berth.longitude})")


def process_movement_message(message):
    allowed_stanox_prefixes = ['04', '12']  # Filter messages to only include a specific regions by STANOX prefix

    header = message['header']
    body = message['body']

    if header['msg_type'] == "0003":  # Movement message
        timestamp = dt.utcfromtimestamp(int(body['actual_timestamp']) / 1000)
        headcode = body['train_id'][2:6]
        toc_id = int(body['toc_id'])

        if toc_id != 0 and body['loc_stanox'][0:2] in allowed_stanox_prefixes:
            trust = Trust(body['train_id'], headcode, toc_id, timestamp)
            db.session.add(trust)
            db.session.commit()


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
