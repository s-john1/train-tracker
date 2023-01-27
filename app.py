import config as conf

from datetime import datetime as dt, timedelta

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote
from sqlalchemy import func, and_

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql://{conf.DB_USER}:%s@{conf.DB_HOST}:{conf.DB_PORT}/{conf.DB_NAME}' \
                                        % quote(conf.DB_PASSWORD)

db = SQLAlchemy(app)


@app.route('/get_trains')
def get_trains():
    query = db.session.query(TrainDescription).filter(TrainDescription.cancelled == 0).all()

    trains = []

    for train in query:
        # For retrieving history
        # previous_locations = []
        # for berth_record in train.berth_history:
        #    previous_locations.append({'lat': berth_record.berth.latitude, 'lon': berth_record.berth.longitude,
        #                               'timestamp': berth_record.timestamp})

        trains.append({'id': train.id,
                       'description': train.description,
                       'lat': train.current_berth.latitude,
                       'lon': train.current_berth.longitude,
                       'timestamp': int((train.last_report - dt(1970, 1, 1)) / timedelta(seconds=1))})

    return jsonify(trains)


if __name__ == '__main__':
    from models import TrainDescription, Trust
    from NROD import NROD

    nrod = NROD(conf.NROD_HOST, conf.NROD_PORT, conf.NROD_USERNAME, conf.NROD_PASSWORD, conf.NROD_SUBSCRIPTION_NAME)

    app.run(host=conf.HOST, port=conf.PORT)
