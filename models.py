from app import db


class Berth(db.Model):
    __tablename__ = "berths"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    describer = db.Column(db.CHAR(2), nullable=False)
    berth = db.Column(db.CHAR(4), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    __table_args__ = (db.UniqueConstraint('describer', 'berth', name='describer_berth'), )

    def __init__(self, describer, berth, latitude, longitude):
        self.describer = describer
        self.berth = berth
        self.latitude = latitude
        self.longitude = longitude

    def __repr__(self):
        return f'Berth(id={self.id}, describer={self.describer}, berth={self.berth}, latitude={self.latitude}, ' \
               f'longitude={self.longitude})'


class TrainDescription(db.Model):
    __tablename__ = "train_descriptions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    describer = db.Column(db.CHAR(2), nullable=False)
    description = db.Column(db.CHAR(4), nullable=False)
    from_berth_id = db.Column(db.Integer, db.ForeignKey(Berth.id), nullable=True)
    to_berth_id = db.Column(db.Integer, db.ForeignKey(Berth.id), nullable=True)
    timestamp = db.Column(db.TIMESTAMP, nullable=False)

    from_berth = db.relationship(Berth, foreign_keys=from_berth_id)
    to_berth = db.relationship(Berth, foreign_keys=to_berth_id)

    def __init__(self, describer, description, timestamp, from_berth_id=None, to_berth_id=None):
        self.describer = describer
        self.description = description
        self.from_berth_id = from_berth_id
        self.to_berth_id = to_berth_id
        self.timestamp = timestamp

    def __repr__(self):
        return f'TrainDescription(id={self.id}, describer={self.describer}, description={self.description}, ' \
               f'from_berth={self.from_berth}, to_berth={self.to_berth}, timestamp={repr(self.timestamp)})'


class Operator(db.Model):
    __tablename__ = "toc_codes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    operator = db.Column(db.String)
    sector_code = db.Column(db.Integer, unique=True)
    atoc_code = db.Column(db.VARCHAR(2), nullable=True)

    def __init__(self, operator, sector_code, atoc_code):
        self.operator = operator
        self.sector_code = sector_code
        self.atoc_code = atoc_code

    def __repr__(self):
        return f'Operator(id={self.id}, operator={self.operator}, sector_code={self.sector_code}, ' \
               f'atoc_code={self.atoc_code})'


class Trust(db.Model):
    __tablename__ = "trust"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    trust_id = db.Column(db.CHAR(10), nullable=False)
    headcode = db.Column(db.CHAR(4), nullable=False)
    toc_id = db.Column(db.Integer, db.ForeignKey(Operator.sector_code), nullable=False)
    timestamp = db.Column(db.TIMESTAMP, nullable=False)

    operator = db.relationship(Operator, foreign_keys=toc_id)

    def __init__(self, trust_id, headcode, toc_id, timestamp):
        self.trust_id = trust_id
        self.headcode = headcode
        self.toc_id = toc_id
        self.timestamp = timestamp

    def __repr__(self):
        return f'Trust(id={self.id}, trust_id={self.trust_id}, toc_id={self.toc_id}, timestamp={repr(self.timestamp)})'


class Smart(db.Model):
    _tablename__ = "smart"

    id = db.Column("id", db.Integer, primary_key=True)
    step_type = db.Column("STEPTYPE", db.CHAR(1), nullable=False)
    from_berth = db.Column("FROMBERTH", db.CHAR(4), nullable=True)
    to_berth = db.Column("TOBERTH", db.CHAR(4), nullable=True)
    stanox = db.Column("STANOX", db.Integer, nullable=False)
    event = db.Column("EVENT", db.CHAR(1), nullable=False)
    platform = db.Column("PLATFORM", db.String, nullable=True)
    to_line = db.Column("TOLINE", db.CHAR(1), nullable=True)
    berth_offset = db.Column("BERTHOFFSET", db.Integer, nullable=False)
    route = db.Column("ROUTE", db.Integer, nullable=True)
    from_line = db.Column("FROMLINE", db.CHAR(1), nullable=True)
    td = db.Column("TD", db.CHAR(2), nullable=False)
    comment = db.Column("COMMENT", db.String, nullable=True)
    stanme = db.Column("STANME", db.String, nullable=True)

    __table__args = (db.ForeignKeyConstraint((td, from_berth), (Berth.describer, Berth.berth)),
                     db.ForeignKeyConstraint((td, to_berth), (Berth.describer, Berth.berth))
                     )

    def __init__(self, step_type,  stanox, event, berth_offset, td, route=None, from_berth=None, to_berth=None,
                 platform=None, to_line=None, from_line=None, comment=None, stanme=None):
        self.step_type = step_type
        self.from_berth = from_berth
        self.to_berth = to_berth
        self.stanox = stanox
        self.event = event
        self.platform = platform
        self.to_line = to_line
        self.berth_offset = berth_offset
        self.route = route
        self.from_line = from_line
        self.td = td
        self.comment = comment
        self.stanme = stanme

    def __repr__(self):
        return f'Smart(step_type={self.step_type}, from_berth={self.from_berth}, to_berth={self.to_berth}, ' \
               f'stanox={self.stanox}, event={self.event}, platform={self.platform}, to_line={self.to_line}, ' \
               f'berth_offset={self.berth_offset}, route={self.route}, from_line={self.from_line}, td={self.td}, ' \
               f'comment={self.comment}, stanme={self.stanme})'


class BerthStep(db.Model):
    __tablename__ = "berth_steps"

    id = db.Column(db.Integer, primary_key=True)
    describer = db.Column(db.CHAR(2), nullable=False)
    from_berth = db.Column(db.CHAR(4), nullable=False)
    to_berth = db.Column(db.CHAR(4), nullable=False)
    count = db.Column(db.Integer, nullable=False)
    last_description = db.Column(db.CHAR(4), nullable=False)
    last_timestamp = db.Column(db.TIMESTAMP, nullable=False)

    __table_args__ = (db.UniqueConstraint('describer', 'from_berth', 'to_berth', name='describer_berths'),)

    def __init__(self, describer, from_berth, to_berth, last_description, last_timestamp):
        self.describer = describer
        self.from_berth = from_berth
        self.to_berth = to_berth
        self.count = 1
        self.last_description = last_description
        self.last_timestamp = last_timestamp

    def __repr__(self):
        return f'BerthStep(id={self.id}, describer={self.describer}, from_berth={self.from_berth}, ' \
               f'to_berth={self.to_berth}, count={self.count}, last_description={self.last_description}, ' \
               f'last_timestamp={self.last_timestamp})'
