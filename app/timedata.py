import configparser
import datetime
from models import *
from config import *


def convert(value):
    """ returns datetime object from '%H:%M' format found in .ini """
    var = datetime.datetime.combine(datetime.date.today(), value)
    return var


def get_seconds(time1, time2):
    """ takes two datetime.datetime objects and returns timedelta.total_seconds()"""
    var = int((time2 - time1).total_seconds())
    var += (86400 if var < 0 else 0)
    return var


class TimeData:
    def __init__(self, shift: str='Day', name: str='Regular'):
        session = create_session('app.db')
        s = session.query(Schedule).filter(Schedule.shift == shift, Schedule.name == name).first()
        # self.start = convert(c['Shift']['start'])
        # self.end = convert(c['Shift']['end'])
        self.id = s.id
        self.available = []
        for i in [s.start1, s.start2, s.start3, s.start4, s.start5, s.start6, s.start7, s.start8]:
            try:
                self.available.append(convert(i))
            except TypeError:
                print('value nonexistent. skipping...')
        self.breaks = []
        for i in [s.end1, s.end2, s.end3, s.end4, s.end5, s.end6, s.end7, s.end8]:
            try:
                self.breaks.append(convert(i))
            except TypeError:
                print('value nonexistent. skipping...')
        self.sched = []
        for i in range(len(self.available)):
            self.sched.append(self.available[i])
            try:
                self.sched.append(self.breaks[i])
            except IndexError:
                self.sched.append(datetime.datetime.combine(datetime.date.today(), datetime.time(15, 0)))
        self.blockSeconds = []
        for i in range(int(len(self.sched)/2)):
            self.blockSeconds.append(get_seconds(self.sched[i * 2], self.sched[i * 2 + 1]))
        self.breakSeconds = []
        for i in range(int(len(self.sched)/2 - 1)):
            self.breakSeconds.append(get_seconds(self.sched[i * 2 + 1], self.sched[i * 2 + 2]))

    def get_sched(self):
        self.sched = []
        for i in range(len(self.available)):
            self.sched.append(self.available[i])
            try:
                self.sched.append(self.breaks[i])
            except IndexError:
                self.sched.append(datetime.datetime.combine(datetime.date.today(), datetime.time(15, 0)))

    def get_block_seconds(self):
        self.blockSeconds = []
        for i in range(int(len(self.sched)/2)):
            self.blockSeconds.append(get_seconds(self.sched[i * 2], self.sched[i * 2 + 1]))

    def get_break_seconds(self):
        self.breakSeconds = []
        for i in range(int(len(self.sched)/2 - 1)):
            self.breakSeconds.append(get_seconds(self.sched[i * 2 + 1], self.sched[i * 2 + 2]))
