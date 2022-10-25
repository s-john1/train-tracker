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
    time_difference = dt.utcnow() - timedelta(hours=1)

    subquery = db.session.query(
        TrainDescription.description, func.max(TrainDescription.timestamp).label('newestTime')
    ).group_by(TrainDescription.description).filter(TrainDescription.timestamp >= time_difference).subquery()

    query = db.session.query(
        TrainDescription
    ).join(subquery,
           and_(
               TrainDescription.description == subquery.c.description,
               TrainDescription.timestamp == subquery.c.newestTime
           ))

    trains = []

    for train in query:
        # Look for matching TRUST entry
        trust = Trust.query.filter_by(headcode=train.description).order_by(Trust.timestamp.desc()).first()

        operator = None
        if trust:
            operator = trust.operator.operator

        trains.append({'description': train.description,
                       'operator': operator,
                       'lat': train.from_berth.latitude,
                       'lon': train.from_berth.longitude,
                       'timestamp': int((train.timestamp - dt(1970, 1, 1)) / timedelta(seconds=1))})

    return jsonify(trains)


if __name__ == '__main__':
    from models import TrainDescription, Trust
    from NROD import NROD

    nrod = NROD(conf.NROD_HOST, conf.NROD_PORT, conf.NROD_USERNAME, conf.NROD_PASSWORD, conf.NROD_SUBSCRIPTION_NAME)

    app.run(host=conf.HOST, port=conf.PORT)

