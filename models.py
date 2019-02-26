from sqlalchemy import Column, ForeignKey, Integer, String, Time, Date, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
import datetime
from config import GUIConfig

Base = declarative_base()
if GUIConfig.platform == 'win32':
    engine = create_engine('sqlite:///app.db')
else:
    engine = create_engine('mysql+pymysql://worker:IYNFYLTalladega@192.168.42.1/timers')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)


class Schedule(Base):
    __tablename__ = 'schedule'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    shift = Column(String(16), nullable=False)
    available_time = Column(Integer)
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

    def get_available_time(self):
        def get_seconds(time1, time2):
            def convert(time):
                var = datetime.datetime.combine(datetime.date.today(), time)
                return var
            seconds = int((convert(time2) - convert(time1)).total_seconds())
            seconds += (86400 if seconds < 0 else 0)
            return seconds
        block_times = []
        for i in [(self.start1, self.end1),
                  (self.start2, self.end2),
                  (self.start3, self.end3),
                  (self.start4, self.end4),
                  (self.start5, self.end5),
                  (self.start6, self.end6),
                  (self.start7, self.end7),
                  (self.start8, self.end8)]:
            if i[0]:
                block_times.append(get_seconds(i[0], i[1]))
        self.available_time = sum(block_times)

    def get_times(self, s1=None, e1=None, s2=None, e2=None, s3=None, e3=None, s4=None, e4=None,
                  s5=None, e5=None, s6=None, e6=None, s7=None, e7=None, s8=None, e8=None):
        self.start1, self.start2, self.start3, self.start4 = s1, s2, s3, s4
        self.start5, self.start6, self.start7, self.start8 = s5, s6, s7, s8
        self.end1, self.end2, self.end3, self.end4 = e1, e2, e3, e4
        self.end5, self.end6, self.end7, self.end8 = e5, e6, e7, e8
        self.get_available_time()

    def return_times(self):
        return (self.start1, self.end1, self.start2, self.end2, self.start3, self.end3,
                self.start4, self.end4, self.start5, self.end5, self.start6, self.end6,
                self.start7, self.end7, self.start8, self.end8)

    def return_schedule(self, kpi_d=datetime.date.today()):
        times = self.return_times()
        new_times = []
        for i in range(len(times)-1, -1, -1):
            time = times[i]
            if type(time) == datetime.time:
                if i < len(times) - 1:
                    if time < times[i+1]:
                        new_time = datetime.datetime.combine(kpi_d, time)
                    else:
                        new_time = datetime.datetime.combine(kpi_d - datetime.timedelta(1), time)
                else:
                    new_time = datetime.datetime.combine(kpi_d, time)
                new_times.insert(0, new_time)
        return new_times

    def __repr__(self):
        return "<Schedule Object '%s' for %s shift>" % (self.name, self.shift)


class KPI(Base):
    __tablename__ = 'kpi'
    id = Column(Integer, primary_key=True)
    d = Column(Date, index=True, nullable=False)
    shift = Column(String(16), index=True, nullable=False)
    demand = Column(Integer)
    delivered = Column(Integer)
    schedule_id = Column(Integer, ForeignKey('schedule.id'))
    schedule = relationship(Schedule)
    plan_cycle_time = Column(Integer)

    def __repr__(self):
        return "<KPI for %s shift on %s>" % (self.shift, self.d)


class Cycles(Base):
    __tablename__ = 'cycles'
    id = Column(Integer, primary_key=True)
    d = Column(DateTime, index=True)
    seq = Column(Integer, index=True)
    cycle_time = Column(Integer)
    parts_per = Column(Integer)
    delivered = Column(Integer)
    hit = Column(Boolean)
    kpi_id = Column(Integer, ForeignKey('kpi.id'))
    kpi = relationship(KPI)

    def __repr__(self):
        return "<Cycle Object %s for seq %s>" % (self.cycle_time, self.seq)


class Operators(Base):
    __tablename__ = 'operators'
    id = Column(Integer, primary_key=True)
    play_name = Column(String(50))
    op_1 = Column(String(50))
    op_2 = Column(String(50))
    op_3 = Column(String(50))
    op_4 = Column(String(50))
    op_5 = Column(String(50))
    op_6 = Column(String(50))
    op_7 = Column(String(50))
    op_8 = Column(String(50))
    op_9 = Column(String(50))
    op_10 = Column(String(50))

    def get_list(self, op_1=None, op_2=None, op_3=None, op_4=None, op_5=None,
                 op_6=None, op_7=None, op_8=None, op_9=None, op_10=None):
        self.op_1, self.op_2, self.op_3, self.op_4, self.op_5,\
            self.op_6, self.op_7, self.op_8, self.op_9, self.op_10 =\
            op_1, op_2, op_3, op_4, op_5, op_6, op_7, op_8, op_9, op_10

    def __repr__(self):
        return "<Operators Object>"


def create_db():
    Base.metadata.create_all(engine)


def create_session():
    """ returns a db session for the given database file """
    # if GUIConfig.platform == 'win32':
    #     engine = create_engine('sqlite:///app.db')
    # else:
    #     engine = create_engine('mysql+pymysql://worker:IYNFYLTalladega@192.168.42.1/timers')
    # Base.metadata.bind = engine
    # DBSession = sessionmaker(bind=engine)
    session = DBSession()
    return session
