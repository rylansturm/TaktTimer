import sys
sys.path.insert(0, '/home/pi/venv/Lib/site-packages')
from models import *
from appJar import gui
from appJar.appjar import ItemLookupError
import datetime
from math import floor


class Var:
    length = 0
    poll_count = 0
    cycles = None
    sequences = []
    kpi = None
    schedule = None
    takt = 0


def shift_guesser():
    return 'Grave' if datetime.datetime.now().hour >= 23 else 'Swing' if datetime.datetime.now().hour >= 15 \
        else 'Day' if datetime.datetime.now().hour >= 7 else 'Grave'


app = gui('tracker', 'fullscreen')
app.setFont(size=20)


def update():
    session = create_session()
    try:
        kpi = session.query(KPI).filter(KPI.shift == shift_guesser(),
                                        KPI.d == datetime.date.today()).one()
        if Var.kpi != kpi:
            Var.kpi = kpi
            Var.schedule = kpi.schedule
            Var.takt = Var.kpi.schedule.available_time / Var.kpi.demand
        Var.cycles = session.query(Cycles).filter(Cycles.kpi_id == Var.kpi.id)
        Var.sequences = []
        for i in Var.cycles.order_by(Cycles.seq.asc()).group_by(Cycles.seq).all():
            Var.sequences.append(i.seq)
        if len(Var.sequences) != Var.length:
            Var.length = len(Var.sequences)
            app.removeAllWidgets()
            app.addLabel('time', datetime.datetime.now().strftime('%I:%M:%S %p'))
            app.getLabelWidget('time').config(font='arial 72')
            for seq in Var.sequences:
                with app.frame('Sequence %s' % seq):
                    app.setSticky('ew')
                    app.addMeter('seq%sMeter' % seq, row=0, column=0, colspan=4)
                    app.setMeterFill('seq%sMeter' % seq, 'green')
                    app.setMeterHeight('seq%sMeter' % seq, 700/Var.length-Var.length*2)
                    app.addLabel('seq%sAVGLabel' % seq, 'Batting AVG: ', 1, 0)
                    app.addLabel('seq%sAVG' % seq, 'avg', 2, 0)
                    # app.addLabel('seq%sEarlyLateLabel' % seq, 'Early - Late', 1, 2)
                    # app.addLabel('seq%sEarlyLate' % seq, 'early-late', 2, 2)
                    app.addLabel('seq%sCurrentLabel' % seq, 'Current', 1, 3)
                    app.addLabel('seq%sCurrent' % seq, 'current', 2, 3)
        for seq in Var.sequences:
            cycle = Var.cycles.filter(Cycles.seq == seq).order_by(Cycles.d.desc())
            avg = '%.3f' % (len(cycle.filter(Cycles.hit == 1).all()) / len(cycle.all()))
            app.setMeter('seq%sMeter' % seq, (cycle.first().delivered / Var.kpi.demand) * 100,
                         'Sequence %s: %s / %s' % (seq, cycle.first().delivered, Var.kpi.demand))
            app.setLabel('seq%sAVG' % seq, avg)
    except NoResultFound:
        print('no KPI found')
    session.close()


def counting():
    now = datetime.datetime.now()
    try:
        app.setLabel('time', now.strftime('%I:%M:%S %p'))
    except ItemLookupError:
        pass
    Var.poll_count += 1
    if Var.poll_count == 10:
        Var.poll_count = 0
        update()
    for seq in Var.sequences:
        cycle = Var.cycles.filter(Cycles.seq == seq).order_by(Cycles.d.desc()).first()
        tCycle = int(floor((Var.takt * cycle.parts_per) - (now - cycle.d).seconds))
        app.setLabel('seq%sCurrent' % seq, tCycle)


app.registerEvent(counting)
app.setPollTime(200)

app.go()
