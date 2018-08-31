import configparser
import datetime


def convert(value):
    """ returns datetime object from '%H:%M' format found in .ini """
    var = datetime.datetime.time(datetime.datetime.strptime(value, '%H:%M'))
    var = datetime.datetime.combine(datetime.date.today(), var)
    return var


def get_seconds(time1, time2):
    """ takes two datetime.datetime objects and returns timedelta.total_seconds()"""
    var = int((time2 - time1).total_seconds())
    var += (86400 if var < 0 else 0)
    return var


class Schedule:
    def __init__(self, file):
        c = configparser.ConfigParser()
        c.read(file)
        self.start = convert(c['Shift']['start'])
        self.end = convert(c['Shift']['end'])
        self.available = []
        for i in c['Available'].values():
            self.available.append(convert(i))
        self.breaks = []
        for i in c['Breaks'].values():
            self.breaks.append(convert(i))
        self.sched = []
        for i in range(len(self.available)):
            self.sched.append(self.available[i])
            try:
                self.sched.append(self.breaks[i])
            except IndexError:
                self.sched.append(self.end)
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
                self.sched.append(self.end)

    def get_block_seconds(self):
        self.blockSeconds = []
        for i in range(int(len(self.sched)/2)):
            self.blockSeconds.append(get_seconds(self.sched[i * 2], self.sched[i * 2 + 1]))

    def get_break_seconds(self):
        self.breakSeconds = []
        for i in range(int(len(self.sched)/2 - 1)):
            self.breakSeconds.append(get_seconds(self.sched[i * 2 + 1], self.sched[i * 2 + 2]))
