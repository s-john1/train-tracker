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

    if "CB_MSG" in message:
        data = message["CB_MSG"]

        # Testing
        if data["area_id"] not in ["EA", "TW", "AL", "MO"]:
            return

        timestamp = dt.utcfromtimestamp(int(data['time']) / 1000)  # timestamp of message from train describer

        print("CB", data["area_id"], data["descr"], data["from"])
        print(data["time"], timestamp)

        # Get berth which has been cancelled
        berth = find_berth(data["area_id"], data["from"])
        if berth:
            print("Berth found")
            # Retrieve train object
            train = get_train(data["area_id"], data["descr"])

            if train and train.current_berth == berth:
                print("Train object found in berth, cancelling")
                train.cancelled = True
                train.active = False
                train.last_report = timestamp

                db.session.commit()
            else:
                print("Train object not found in berth")
        else:
            print("Berth not found, discarding")

    elif "CA_MSG" in message:
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

        timestamp = dt.utcfromtimestamp(int(data['time']) / 1000)  # timestamp of message from train describer

        print(data["area_id"], data["descr"], data["from"], data["to"])
        print(data["time"], timestamp)

        # Retrieve train object
        train = get_train(data["area_id"], data["descr"])

        if train is None:
            print("Train object doesn't exist")

            if to_berth:
                print("To berth exists")

                # Check if berth borders another TD (i.e. train has just entered this TD)
                if to_berth.borders_prev_describer:
                    print("Borders previous describer", to_berth.borders_prev_describer)

                    # Attempt to find this train's objects in the previous describer
                    #   (It's possible the previous describer hasn't yet sent the message that this
                    #   train is leaving its area)
                    train = get_train(to_berth.borders_prev_describer, data["descr"])
                    if train:
                        print("Train object exists in bordering describer", train)
                        # Update to berth and timestamp. Don't update describer here as this should
                        #   be handled when the train steps out the bordering describer
                        set_current_berth(train, to_berth)
                        train.last_report = timestamp
                        train.active = True

                        db.session.commit()

                        # Return early, we assume we don't need to consider the 'from' berth in these cases
                        print()
                        return

                # Train object doesn't exist, create one
                print("Create train object, train active")
                check_train_in_berth(to_berth)
                train = TrainDescription(data["area_id"], data["descr"], to_berth, timestamp)
                db.session.add(train)

                train.active = True
            else:
                print("To berth doesn't exist")
                # If to berth doesn't exist, from berth must exist here
                # Train object doesn't exist, create one
                print("Create train object, train inactive")
                check_train_in_berth(from_berth)
                train = TrainDescription(data["area_id"], data["descr"], from_berth, timestamp)
                db.session.add(train)

                train.active = False

            # Add/update train to database
            db.session.commit()

        else:
            # Train object already exists
            print("Train object already exists")

            if to_berth:
                print("To berth found, train active")

                # Discard message if to berth already matches (likely duplicate message)
                if train.current_berth.id == to_berth.id:
                    print("Discarding message - berth already matches")
                    print()
                    return

                set_current_berth(train, to_berth)
                train.active = True
            else:
                print("To berth not found, train inactive")
                train.active = False
                # If to berth doesn't exist, from berth must exist here
                set_current_berth(train, from_berth)

            # Update timestamp
            train.last_report = timestamp

        # Check from berth
        if from_berth:
            print("From berth found")

            # Create berth history record
            history_record = BerthRecord(train.id, from_berth.id, timestamp)
            db.session.add(history_record)
            db.session.commit()

            # If berth borders another train describer
            if from_berth.borders_next_describer:
                print("Borders next describer", from_berth.borders_next_describer)
                train.describer = from_berth.borders_next_describer  # Update for next train describer

                # Assume train is active as bordering berths should be mapped
                train.active = True

        db.session.commit()
        print(train)
        print()


def get_train(area, description):
    query = db.session.query(TrainDescription).filter(
        TrainDescription.describer == area,
        TrainDescription.description == description,
        TrainDescription.cancelled == 0)

    return query.first()


def check_train_in_berth(berth):
    # Check for any trains already occupying this berth
    train = db.session.query(TrainDescription).filter(TrainDescription.cancelled == 0,
                                                      TrainDescription.current_berth == berth).first()
    if train:
        # Cancel the train if its already occupying the berth
        print("Train currently in berth, cancelling it", train)
        train.active = False
        train.cancelled = True

    db.session.commit()


def set_current_berth(train, berth):
    # Remove any trains already in this berth
    check_train_in_berth(berth)

    # Update current berth
    train.current_berth = berth


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

        self.conn = stomp.Connection12([(host, port)], keepalive=True, heartbeats=(15000, 15000))
        self.conn.set_listener('', Listener(self.conn, self.connect_and_subscribe))
        self.connect_and_subscribe()

    def connect_and_subscribe(self):
        self.conn.connect(**{
            "username": self._username,
            "passcode": self._password,
            "wait": True,
            "client-id": self._username + '-' + self._subscription_name
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
