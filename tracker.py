import sys
sys.path.insert(0, '/home/pi/TaktTimer/venv/Lib/site-packages')
from models import *
from appJar import gui
from appJar.appjar import ItemLookupError
from sqlalchemy.orm.exc import NoResultFound
import datetime


class Var:
    length = 1
    poll_count = 0
    cycles = None
    sequences = []
    labels_swing = {1: 'Assembly',
                    2: 'Presses',
                    3: 'Blaster',
                    4: 'Lapper',
                    5: 'Pre-Size',
                    6: 'Bonder',
                    7: 'Pre-Finish',
                    8: 'Chamfer',
                    }
    labels_day = {1: 'Assembly',
                  2: 'Presses',
                  3: 'Blaster',
                  4: 'Lapper',
                  5: 'Pre-Size',
                  6: 'Bonder',
                  7: 'Pre-Finish',
                  8: 'Chamfer',
                  }
    kpi = None
    schedule = None
    takt = 0
    demand = 0
    tct = {}
    breaktime = False
    overall_stability = 0.0


def shift_guesser():
    return 'Grave' if datetime.datetime.now().hour >= 23 else 'Swing' if datetime.datetime.now().hour >= 15 \
        else 'Day' if datetime.datetime.now().hour >= 7 else 'Grave'


app = gui('tracker', 'fullscreen')
app.setFont(size=20)
app.setBg(GUIConfig.appBgColor)
session = create_session()


def update():
    try:
        if shift_guesser() == 'Grave' and datetime.datetime.time(datetime.datetime.now()) < datetime.time(12, 0):
            date = datetime.date.today() - datetime.timedelta(days=1)
        else:
            date = datetime.date.today()
        kpi = session.query(KPI).filter(KPI.shift == shift_guesser(),
                                        KPI.d == date).one()
        if Var.kpi != kpi:
            Var.kpi = kpi
            Var.schedule = kpi.schedule
            Var.takt = Var.kpi.schedule.available_time / Var.kpi.demand
            Var.demand = Var.kpi.demand
        Var.cycles = session.query(Cycles).filter(Cycles.kpi_id == Var.kpi.id)
        Var.sequences = []
        for i in Var.cycles.order_by(Cycles.seq.asc()).group_by(Cycles.seq).all():
            Var.sequences.append(i.seq)
        if len(Var.sequences) != Var.length:
            Var.length = len(Var.sequences)
            app.removeAllWidgets()
            app.addLabel('time', datetime.datetime.now().strftime('%I:%M:%S %p'), row=0, column=0)
            app.addLabel('overallStability', 'Shift Stability: 0', row=0, column=1)
            app.addLabel('onOffTrackLabel', 'Current Expectation: 0\n Demand: 0', colspan=2)
            app.getLabelWidget('time').config(font='arial 48')
            try:
                Var.overall_stability = (len(Var.cycles.filter(Cycles.hit == 1).all()) /
                                         len(Var.cycles.all())) * 100
            except ZeroDivisionError:
                Var.overall_stability = 0.0
            app.setLabel('overallStability', 'On Time Delivery: %i%%' % Var.overall_stability)
            for seq in Var.sequences:
                with app.frame('Sequence %s' % seq, colspan=2):
                    app.setSticky('ew')
                    app.addMeter('seq%sMeter' % seq, row=0, column=0, colspan=4)
                    app.setMeterFill('seq%sMeter' % seq, 'green')
                    app.setMeterHeight('seq%sMeter' % seq, 500/Var.length-Var.length*2)
                    # app.addLabel('seq%sAVGLabel' % seq, 'Stability: ', 1, 0)
                    app.addLabel('seq%sAVG' % seq, 'On Time Delivery: 0%', 2, 0)
                    # app.addLabel('seq%sEarlyLateLabel' % seq, 'Early - Late', 1, 2)
                    # app.addLabel('seq%sEarlyLate' % seq, 'early-late', 2, 2)
                    # app.addLabel('seq%sCurrentLabel' % seq, 'Current', 1, 3)
                    app.addLabel('seq%sCurrent' % seq, 'Current Timer: 0', 2, 3)
        try:
            expected = int(time_elapsed() // Var.takt)
        except ZeroDivisionError:
            expected = 0
        for seq in Var.sequences:
            label = Var.labels_swing[seq] if shift_guesser() == 'Swing' else Var.labels_day[seq]
            seq_cycles = Var.cycles.filter(Cycles.seq == seq).order_by(Cycles.d.desc())
            delivered = seq_cycles.first().delivered
            ahead = delivered - expected
            ahead = (('+' + str(ahead)) if ahead > 0 else str(ahead))
            avg = 'On Time Delivery %i%%' % \
                  (len(seq_cycles.filter(Cycles.hit == 1).all()) / len(seq_cycles.all()) * 100)
            app.setMeter('seq%sMeter' % seq, (seq_cycles.first().delivered / Var.kpi.demand) * 100,
                         '%s:     %s  (%s)' %
                         (label, delivered, ahead))
            app.setLabel('seq%sAVG' % seq, avg)
            Var.tct[seq] = get_tct(seq_cycles.first().delivered)
            Var.tct[seq] = get_tct(seq_cycles.first().delivered)
        try:
            app.setLabel('overallStability', 'On Time Delivery: %i%%' % Var.overall_stability)
            app.setLabel('onOffTrackLabel',
                         'Current Expectation: %s\n\t  Demand: %s' % (int(time_elapsed() // Var.takt), Var.demand))
        except ItemLookupError:
            pass
    except NoResultFound:
        print('no KPI found')
    session.close()


def get_tct(parts_out):
    try:
        remaining_demand = Var.demand - parts_out
        remaining_time = Var.schedule.available_time - time_elapsed()
    except AttributeError:
        return Var.takt
    try:
        tct = remaining_time // remaining_demand
    except ZeroDivisionError:
        tct = Var.takt
    if tct < 45:
        return 45
    elif tct > Var.takt:
        return Var.takt
    else:
        return int(tct)


def get_block_var():
    now = datetime.datetime.time(datetime.datetime.now())
    sched = []
    for time in Var.schedule.return_times():
        if time:
            sched.append(time)
    var = 0
    if shift_guesser() == 'Grave':
        if now > sched[0]:
            var = 1
        else:
            var = 1
            for time in sched[1:]:
                if now > time:
                    var += 1
    else:
        for time in sched:
            if now > time:
                var += 1
    Var.breaktime = True if var % 2 == 0 else False
    return var


def reset():
    Var.length = 0
    Var.poll_count = 0
    Var.cycles = None
    Var.sequences = []
    Var.kpi = None
    Var.schedule = None
    Var.takt = 0
    Var.demand = 0
    Var.tct = {}


def time_elapsed():
    now = datetime.datetime.now()
    block = get_block_var()
    sched = []
    for time in Var.schedule.return_times():
        if time:
            sched.append(time)
    if block >= len(sched):
        reset()
        return 0
    elapsed = (now - datetime.datetime.combine(datetime.date.today(), sched[0])).total_seconds()
    for i in range(len(sched) // 2 - 1):
        if sched[2*i+2]:
            seconds_in_break = (datetime.datetime.combine(datetime.date.today(), sched[2 * i + 2])
                                - datetime.datetime.combine(datetime.date.today(), sched[2 * i + 1])).total_seconds()
            if block/2 > i+1:
                elapsed -= seconds_in_break
    if block % 2 == 0:
        elapsed -= (now - datetime.datetime.combine(datetime.date.today(), sched[block - 1])).total_seconds()
    elapsed += (86400 if elapsed < 0 else 0)
    return elapsed


def counting():
    now = datetime.datetime.now()
    try:
        app.setLabel('time', now.strftime('%I:%M:%S %p'))
    except ItemLookupError:
        pass
    Var.poll_count += 1
    if Var.poll_count == 15:
        Var.poll_count = 0
        update()
    for seq in Var.sequences:
        cycle = Var.cycles.filter(Cycles.seq == seq).order_by(Cycles.d.desc()).first()
        tCycle = int((Var.tct[seq] * cycle.parts_per) - (now - cycle.d).seconds)
        if get_block_var() % 2 != 0:
            app.setLabel('seq%sCurrent' % seq, 'Current Timer: %s' % tCycle)
            if tCycle < 0 and app.getLabelBg('seq%sCurrent' % seq) != GUIConfig.andonColor:
                app.setLabelBg('seq%sCurrent' % seq, GUIConfig.andonColor)
            if tCycle > 0 and app.getLabelBg('seq%sCurrent' % seq) != GUIConfig.appBgColor:
                app.setLabelBg('seq%sCurrent' % seq, GUIConfig.appBgColor)


app.registerEvent(counting)
app.setPollTime(200)

app.go()
