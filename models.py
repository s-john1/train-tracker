from app import db


class Berth(db.Model):
    __tablename__ = "berths"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    describer = db.Column(db.CHAR(2), nullable=False)
    berth = db.Column(db.CHAR(4), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    borders_describer = db.Column(db.CHAR(2), nullable=True)

    __table_args__ = (db.UniqueConstraint('describer', 'berth', name='describer_berth'), )

    def __init__(self, describer, berth, latitude, longitude, borders_describer=None):
        self.describer = describer
        self.berth = berth
        self.latitude = latitude
        self.longitude = longitude
        self.borders_describer = borders_describer

    def __repr__(self):
        return f'Berth(id={self.id}, describer={self.describer}, berth={self.berth}, latitude={self.latitude}, ' \
               f'longitude={self.longitude}, borders_describer={self.borders_describer})'


class TrainDescription(db.Model):
    __tablename__ = "train_descriptions_new"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    describer = db.Column(db.CHAR(2), nullable=False)
    description = db.Column(db.CHAR(4), nullable=False)
    current_berth_id = db.Column(db.Integer, db.ForeignKey(Berth.id), nullable=True)
    last_report = db.Column(db.TIMESTAMP, nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    cancelled = db.Column(db.Boolean, default=False, nullable=False)

    current_berth = db.relationship(Berth, foreign_keys=current_berth_id)

    def __init__(self, describer, description, current_berth_id, last_report, active=True, cancelled=False):
        self.describer = describer
        self.description = description
        self.current_berth_id = current_berth_id
        self.last_report = last_report
        self.active = active
        self.cancelled = cancelled

    def __repr__(self):
        return f'TrainDescription(id={self.id}, describer={self.describer}, description={self.description}, ' \
               f'current_berth={self.current_berth}, last_report={repr(self.last_report)}, active={self.active}, ' \
               f'cancelled={self.cancelled})'


class BerthRecord(db.Model):
    __tablename__ = "berth_history"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    train_id = db.Column(db.Integer, db.ForeignKey(TrainDescription.id), nullable=False)
    berth_id = db.Column(db.Integer, db.ForeignKey(Berth.id), nullable=False)
    timestamp = db.Column(db.TIMESTAMP, nullable=False)

    train = db.relationship(TrainDescription, foreign_keys=train_id)
    berth = db.relationship(Berth, foreign_keys=berth_id)

    def __init__(self, train_id, berth_id, timestamp):
        self.train_id = train_id
        self.berth_id = berth_id
        self.timestamp = timestamp

    def __repr__(self):
        return f'BerthRecord(id={self.id}, train={self.train}, berth={self.berth}, timestamp={repr(self.timestamp)})'


class Operator(db.Model):
    __tablename__ = "toc_codes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    operator = db.Column(db.String)
    sector_code = db.Column(db.Integer, unique=True)

    def __init__(self, operator, sector_code):
        self.operator = operator
        self.sector_code = sector_code

    def __repr__(self):
        return f'Operator(id={self.id}, operator={self.operator}, sector_code={self.sector_code})'


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
