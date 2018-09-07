from sqlalchemy import Column, ForeignKey, Integer, String, Time, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class Schedule(Base):
    __tablename__ = 'schedule'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    shift = Column(String(16), nullable=False)
    start1 = Column(Time, nullable=False)
    end1 = Column(Time, nullable=False)
    start2 = Column(Time, nullable=True)
    end2 = Column(Time, nullable=True)
    start3 = Column(Time, nullable=True)
    end3 = Column(Time, nullable=True)
    start4 = Column(Time, nullable=True)
    end4 = Column(Time, nullable=True)
    start5 = Column(Time, nullable=True)
    end5 = Column(Time, nullable=True)
    start6 = Column(Time, nullable=True)
    end6 = Column(Time, nullable=True)
    start7 = Column(Time, nullable=True)
    end7 = Column(Time, nullable=True)
    start8 = Column(Time, nullable=True)
    end8 = Column(Time, nullable=True)

    def __repr__(self):
        return "<Schedule Object '%s' for %s shift>" % (self.name, self.shift)


class KPI(Base):
    __tablename__ = 'kpi'
    id = Column(Integer, primary_key=True)
    d = Column(Date, index=True,nullable=False)
    shift = Column(String(16), index=True, nullable=False)
    schedule_id = Column(Integer, ForeignKey('schedule.id'))
    demand = Column(Integer)
    delivered = Column(Integer)

    def __repr__(self):
        return "<KPI for %s shift on %s>" % (self.shift, self.d)


class Cycles(Base):
    __tablename__ = 'cycles'
    id = Column(Integer, primary_key=True)
    d = Column(DateTime, index=True)
    seq = Column(Integer, index=True)
    cycle_time = Column(Integer)

    def __repr__(self):
        return "<Cycle Object %s for seq %s>" % (self.cycle_time, self.seq)


def create_db(file):
    engine = create_engine('sqlite:///%s.db' % file)
    Base.metadata.create_all(engine)

