import sys
sys.path.insert(0, '/home/pi/TaktTimer/venv/Lib/site-packages')
from models import *
from appJar import gui
from appJar.appjar import ItemLookupError
from sqlalchemy.orm.exc import NoResultFound
import datetime


class Var:
    length = 0
    poll_count = 0
    cycles = None
    sequences = []
    kpi = None
    schedule = None
    takt = 0
    demand = 0
    tct = {}


def shift_guesser():
    return 'Grave' if datetime.datetime.now().hour >= 23 else 'Swing' if datetime.datetime.now().hour >= 15 \
        else 'Day' if datetime.datetime.now().hour >= 7 else 'Grave'


app = gui('tracker', 'fullscreen')
app.setFont(size=20)
app.setBg(GUIConfig.appBgColor)
session = create_session()


def update():
    try:
        kpi = session.query(KPI).filter(KPI.shift == shift_guesser(),
                                        KPI.d == datetime.date.today()).one()
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
            app.getLabelWidget('time').config(font='arial 48')
            for seq in Var.sequences:
                with app.frame('Sequence %s' % seq, colspan=2):
                    app.setSticky('ew')
                    app.addMeter('seq%sMeter' % seq, row=0, column=0, colspan=4)
                    app.setMeterFill('seq%sMeter' % seq, 'green')
                    app.setMeterHeight('seq%sMeter' % seq, 500/Var.length-Var.length*2)
                    app.addLabel('seq%sAVGLabel' % seq, 'Stability: ', 1, 0)
                    app.addLabel('seq%sAVG' % seq, 'avg', 2, 0)
                    # app.addLabel('seq%sEarlyLateLabel' % seq, 'Early - Late', 1, 2)
                    # app.addLabel('seq%sEarlyLate' % seq, 'early-late', 2, 2)
                    app.addLabel('seq%sCurrentLabel' % seq, 'Current', 1, 3)
                    app.addLabel('seq%sCurrent' % seq, 'current', 2, 3)
        for seq in Var.sequences:
            seq_cycles = Var.cycles.filter(Cycles.seq == seq).order_by(Cycles.d.desc())
            avg = '%.3f' % (len(seq_cycles.filter(Cycles.hit == 1).all()) / len(seq_cycles.all()))
            app.setMeter('seq%sMeter' % seq, (seq_cycles.first().delivered / Var.kpi.demand) * 100,
                         'Sequence %s: (%s / %s) / %s' %
                         (seq, seq_cycles.first().delivered, int(time_elapsed() // Var.takt), Var.kpi.demand))
            app.setLabel('seq%sAVG' % seq, avg)
            Var.tct[seq] = get_tct(seq_cycles.first().delivered)
            Var.tct[seq] = get_tct(seq_cycles.first().delivered)
        Var.overall_stability = len(Var.cycles.filter(Cycles.hit == 1).all()) / len(Var.cycles.all())
        app.setLabel('overallStability', 'Shift Stability:\n     %.3f' % Var.overall_stability)
    except NoResultFound:
        print('no KPI found')
    session.close()


def get_tct(parts_out):
    remaining_demand = Var.demand - parts_out
    remaining_time = Var.schedule.available_time - time_elapsed()
    tct = remaining_time // remaining_demand
    if tct < 45:
        return 45
    elif tct > Var.takt:
        return Var.takt
    else:
        return int(tct)


def get_block_var():
    sched = Var.schedule.return_times()
    var = 0
    for time in sched:
        if time:
            if datetime.datetime.time(datetime.datetime.now()) > time:
                var += 1
    return var


def time_elapsed():
    now = datetime.datetime.now()
    block = get_block_var()
    sched = Var.schedule.return_times()
    elapsed = (now - datetime.datetime.combine(datetime.date.today(), sched[0])).total_seconds()
    for i in range(len(sched) // 2 - 1):
        if sched[2*i+2]:
            seconds_in_break = (datetime.datetime.combine(datetime.date.today(), sched[2 * i + 2])
                                - datetime.datetime.combine(datetime.date.today(), sched[2 * i + 1])).total_seconds()
            if block/2 > i+1:
                elapsed -= seconds_in_break
    if block % 2 == 0:
        elapsed -= (now - datetime.datetime.combine(datetime.date.today(), sched[block - 1])).total_seconds()
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
            app.setLabel('seq%sCurrent' % seq, tCycle)
            if tCycle < 0 and app.getLabelBg('seq%sCurrent' % seq) != GUIConfig.andonColor:
                app.setLabelBg('seq%sCurrent' % seq, GUIConfig.andonColor)
            if tCycle > 0 and app.getLabelBg('seq%sCurrent' % seq) != GUIConfig.appBgColor:
                app.setLabelBg('seq%sCurrent' % seq, GUIConfig.appBgColor)


app.registerEvent(counting)
app.setPollTime(200)

app.go()
