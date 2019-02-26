import sys
sys.path.insert(0, '/home/pi/TaktTimer/venv/Lib/site-packages')
from models import *
from appJar import gui
from appJar.appjar import ItemLookupError
from sqlalchemy.orm.exc import NoResultFound
import datetime


class Var:
    length = 0
    poll_count = 10
    cycles = None
    sequences = []
    labels = {1: 'Sequence 1',
              2: 'Sequence 2',
              3: 'Sequence 3',
              4: 'Sequence 4',
              5: 'Sequence 5',
              6: 'Sequence 6',
              7: 'Sequence 7',
              8: 'Sequence 8',
              9: 'Sequence 9',
              }
    kpi = None
    schedule = None
    sched = []
    takt = 0
    demand = 0
    tct = {}
    tct_from_kpi = None
    breaktime = False
    overall_stability = 0.0
    seq_meter_values = {}
    block_available_time = 6000


def shift_guesser():
    return 'Grave' if datetime.datetime.now().hour >= 23 else 'Swing' if datetime.datetime.now().hour >= 15 \
        else 'Day' if datetime.datetime.now().hour >= 7 else 'Grave'


app = gui('tracker', 'fullscreen')
app.setFont(size=20)
app.setBg(GUIConfig.appBgColor)
session = create_session()

app.addLabel('time', datetime.datetime.now().strftime('%I:%M:%S %p'), row=0, column=0)
app.addLabel('overallStability', 'Shift Stability: 0', row=0, column=1)
app.addLabel('onOffTrackLabel', 'Current Expectation: 0\n Demand: 0', colspan=2)
app.getLabelWidget('time').config(font='arial 48')


def update():
    print('update')
    try:
        kpi = session.query(KPI).filter(KPI.shift == shift_guesser(),
                                        KPI.d == kpi_date()).one()
        if Var.kpi != kpi:
            Var.kpi = kpi
            Var.schedule = kpi.schedule
            Var.tct_from_kpi = kpi.plan_cycle_time
            try:
                Var.takt = Var.kpi.schedule.available_time / Var.kpi.demand
            except ZeroDivisionError:
                Var.takt = 60
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
                    try:
                        height = 500/Var.length-Var.length*2
                    except ZeroDivisionError:
                        height = 100
                    app.setSticky('ew')
                    app.addMeter('seq%sMeter' % seq, row=0, column=0, colspan=4)
                    app.setMeterFill('seq%sMeter' % seq, 'green')
                    app.setMeterHeight('seq%sMeter' % seq, height)
                    # app.addLabel('seq%sAVGLabel' % seq, 'Stability: ', 1, 0)
                    app.addLabel('seq%sAVG' % seq, 'On Time Delivery: 0%', 2, 0)
                    # app.addLabel('seq%sEarlyLateLabel' % seq, 'Early - Late', 1, 2)
                    # app.addLabel('seq%sEarlyLate' % seq, 'early-late', 2, 2)
                    # app.addLabel('seq%sCurrentLabel' % seq, 'Current', 1, 3)
                    app.addLabel('seq%sCurrent' % seq, 'Current Timer: 0', 2, 3)
        try:
            expected = int(time_elapsed() // Var.takt)
        except ZeroDivisionError:
            expected = 1
        try:
            for seq in Var.sequences:
                label = Var.labels[seq]
                seq_cycles = Var.cycles.filter(Cycles.seq == seq).order_by(Cycles.d.desc())
                delivered = seq_cycles.first().delivered
                ahead = delivered - expected
                ahead = (('+' + str(ahead)) if ahead > 0 else str(ahead))
                try:
                    avg = 'On Time Delivery %i%%' % \
                          (len(seq_cycles.filter(Cycles.hit == 1).all()) / len(seq_cycles.all()) * 100)
                except ZeroDivisionError:
                    avg = 'On Time Delivery 0%%'
                # try:
                #     app.setMeter('seq%sMeter' % seq, (seq_cycles.first().delivered / Var.kpi.demand) * 100,
                #                  '%s:     %s  (%s)' %
                #                  (label, delivered, ahead))
                # except ZeroDivisionError:
                #     app.setMeter('seq%sMeter' % seq, 0.0, 'Sequence:     0   (0)')
                app.setLabel('seq%sAVG' % seq, avg)
                Var.tct[seq] = get_tct(seq_cycles.first().delivered)
                Var.tct[seq] = get_tct(seq_cycles.first().delivered)
        except AttributeError:
            pass
        try:
            app.setLabel('overallStability', 'On Time Delivery: %i%%' % Var.overall_stability)
            app.setLabel('onOffTrackLabel',
                         'Current Expectation: %s\n\t  Demand: %s' % (int(time_elapsed() // Var.takt), Var.demand))
        except ItemLookupError or ZeroDivisionError:
            pass
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
    if Var.poll_count == 15:
        Var.poll_count = 0
        update()
    try:
        expected = int(time_elapsed() // Var.takt)
    except ZeroDivisionError:
        expected = 0
    except AttributeError:
        expected = 0
    except IndexError:
        expected = 0
    try:
        for seq in Var.sequences:
            meter = 'seq%sMeter' % seq
            cycle = Var.cycles.filter(Cycles.seq == seq).order_by(Cycles.d.desc()).first()
            tCycle = int((Var.tct[seq] * cycle.parts_per) - (now - cycle.d).seconds)
            if get_block_var() % 2 != 0:
                # Var.block_available_time = (datetime.datetime.now() - Var.sched[get_block_var()-1]).total_seconds()
                app.setLabel('seq%sCurrent' % seq, 'Current Timer: %s' % countdown_format(tCycle))
                if tCycle < 0 and app.getLabelBg('seq%sCurrent' % seq) != GUIConfig.andonColor:
                    app.setLabelBg('seq%sCurrent' % seq, GUIConfig.andonColor)
                if tCycle > 0 and app.getLabelBg('seq%sCurrent' % seq) != GUIConfig.appBgColor:
                    app.setLabelBg('seq%sCurrent' % seq, GUIConfig.appBgColor)
            label = Var.labels[seq]
            seq_cycles = Var.cycles.filter(Cycles.seq == seq).order_by(Cycles.d.desc())
            delivered = seq_cycles.first().delivered
            expected_cycles = expected // cycle.parts_per
            delivered_cycles = delivered // cycle.parts_per
            ahead = delivered_cycles - expected_cycles
            ahead = (('+' + str(ahead)) if ahead > 0 else str(ahead))
            try:
                meter_val = (delivered_cycles / (Var.kpi.demand / cycle.parts_per)) * 100
                meter_val = 100.0 if meter_val > 100 else meter_val
            except ZeroDivisionError:
                meter_val = 0.0
            meter_label = ('%s:     %s / %s Cycles (%s)' % (label, delivered_cycles, expected_cycles, ahead))
            Var.seq_meter_values[meter] = (meter_val/100, meter_label)
            if app.getMeter(meter) != Var.seq_meter_values[meter]:
                print(Var.seq_meter_values)
                print(app.getMeter(meter))
                app.setMeter(meter, meter_val, meter_label)
    except AttributeError:
        print(AttributeError)
        pass


def countdown_format(seconds: int):
    """ takes seconds and returns ":SS", "MM:SS", or "HH:MM:SS" """
    sign = -1 if seconds < 0 else 1
    seconds = seconds * sign
    sign_label = '-' if sign < 0 else ''
    hours, minutes = divmod(seconds, 3600)
    minutes, seconds = divmod(minutes, 60)
    hour_label = '%sh:%02d' % (hours, minutes)
    minute_label = '%s:%02d' % (minutes, seconds)
    second_label = sign_label + ':%02d' % seconds
    return seconds if hours < 0 else hour_label if hours else minute_label if minutes else second_label


def key_press(key):
    """ handles physical key presses (keyboard or pedal) """
    if key == '<F11>':
        app.exitFullscreen() if app.getFullscreen() else app.setFullscreen()


app.bindKey('<F11>', key_press)


def get_tct(parts_out):
    if Var.tct_from_kpi:
        return Var.tct_from_kpi
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
    Var.sched = []
    try:
        for time in Var.schedule.return_times():
            if time:
                Var.sched.append(time)
    except AttributeError:
        pass
    var = 0
    try:
        if shift_guesser() == 'Grave':
            if now > Var.sched[0]:
                var = 1
            else:
                var = 1
                for time in Var.sched[1:]:
                    if now > time:
                        var += 1
        else:
            for time in Var.sched:
                if now > time:
                    var += 1
    except IndexError:
        var = 0
    Var.breaktime = True if var % 2 == 0 else False
    return var


def reset():
    Var.length = 0
    Var.poll_count = 0
    Var.cycles = None
    Var.sequences = []
    Var.kpi = None
    Var.schedule = None
    Var.takt = 1
    Var.demand = 0
    Var.tct = {}


def time_elapsed():
    try:
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
    except AttributeError:
        return 0


def kpi_date():
    """ returns the date used by the kpi table, which is the date the shift ends """
    date = datetime.date.today()  # Current date
    if datetime.datetime.now().hour >= 23:  # if it's before midnight on Grave
        date += datetime.timedelta(days=1)  # use the end date
    return date


app.registerEvent(counting)
app.setPollTime(200)

app.go()
