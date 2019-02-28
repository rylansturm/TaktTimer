import sys
sys.path.insert(0, '/home/pi/TaktTimer/venv/Lib/site-packages')
from models import *
from appJar import gui
from appJar.appjar import ItemLookupError
from sqlalchemy.orm.exc import NoResultFound
import datetime
import requests
import configparser

c = configparser.ConfigParser()
c.read('install.ini')

if 'area' not in c['Var']:
    c['Var']['area'] = 'Talladega'
    with open('install.ini', 'w') as configfile:
        c.write(configfile)


class Var:
    area = c['Var']['area']
    length = 0
    poll_count = 10
    cycles = None
    sequences = []
    data = {}
    if area == 'Talladega':
        labels = {1: 'Assembly  ',
                  2: 'Presses   ',
                  3: 'Blaster   ',
                  4: 'Lapping   ',
                  5: 'Pre-Size  ',
                  6: 'Bonder    ',
                  7: 'Finish CG ',
                  8: 'Chamfers  ',
                  9: 'Sequence 9',
                  }
    else:
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


def get_block_data():
    area = Var.area
    shift = shift_guesser()
    date = kpi_date()
    block = (get_block_var() // 2) + 1
    r = requests.get('https://andonresponse.com/api/cycles/block_tracker/{}/{}/{}/{}'.format(
        area, shift, date, block), verify=False)
    return r.json()


def shift_guesser():
    return 'Grave' if datetime.datetime.now().hour >= 23 else 'Swing' if datetime.datetime.now().hour >= 15 \
        else 'Day' if datetime.datetime.now().hour >= 7 else 'Grave'


app = gui('tracker', 'fullscreen')
app.setFont(size=20)
app.setBg(GUIConfig.appBgColor)
session = create_session()

app.addLabel('time', datetime.datetime.now().strftime('%I:%M:%S %p'), row=0, column=0)
app.addLabel('overallStability', 'Shift Stability: 0', row=0, column=1)
app.addLabel('header', 'Cycles Completed Per Sequence This Block', colspan=2)
app.getLabelWidget('header').config(font='arial 32')
app.getLabelWidget('time').config(font='arial 48')


def update():
    print('update')
    Var.data = get_block_data()
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
            app.addLabel('header', 'Cycles Completed Per Sequence This Block', colspan=2)
            app.getLabelWidget('header').config(font='arial 32')
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
                    app.addLabel('seq%sAndons' % seq, '0 Andons', 1, 0)
                    app.setLabelFg('seq%sAndons' % seq, 'white')
                    app.addLabel('seq%sAVG' % seq, 'On Time: 0%', 1, 1)
                    app.addLabel('seq%sCurrent' % seq, 'Current Timer: 0', 1, 3)
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
                Var.block_available_time = time_dif(Var.sched[get_block_var()-1],
                                                    Var.sched[get_block_var()])
                Var.block_time_elapsed = time_dif(Var.sched[get_block_var()-1],
                                                  datetime.datetime.now())
                seq_cycles = Var.cycles.filter(Cycles.seq == seq).order_by(Cycles.d.desc())
                delivered = seq_cycles.first().delivered
                if Var.tct_from_kpi:
                    total_expected_block_cycles = Var.block_available_time // (Var.tct_from_kpi * cycle.parts_per)
                    current_expected_block_cycles = Var.block_time_elapsed // (Var.tct_from_kpi * cycle.parts_per)
                else:
                    total_expected_block_cycles = Var.block_available_time // (Var.takt * cycle.parts_per)
                    current_expected_block_cycles = Var.block_time_elapsed // (Var.takt * cycle.parts_per)
                delivered_block_cycles = seq_cycles.filter(Cycles.d >= Var.sched[get_block_var()-1],
                                                           Cycles.d <= Var.sched[get_block_var()]).count()
                try:
                    andons = Var.data[str(seq)]['Andons']
                    responded = Var.data[str(seq)]['Responded']
                except KeyError:
                    andons = 0
                    responded = True
                if not responded and app.getLabelBg('seq%sAndons' % seq) != GUIConfig.andonColor:
                    app.setLabelBg('seq%sAndons' % seq, GUIConfig.andonColor)
                if responded and app.getLabelBg('seq%sAndons' % seq) != 'green':
                    app.setLabelBg('seq%sAndons' % seq, 'green')
                app.setLabel('seq%sAndons' % seq, '%s Andons' % andons)
                ahead = int(delivered_block_cycles - current_expected_block_cycles)
                ahead = (('+' + str(ahead)) if ahead > 0 else str(ahead))
                app.setLabel('seq%sCurrent' % seq, 'Current Timer: %s' % countdown_format(tCycle))
                if tCycle < 0 and app.getLabelBg('seq%sCurrent' % seq) != GUIConfig.andonColor:
                    app.setLabelBg('seq%sCurrent' % seq, GUIConfig.andonColor)
                if tCycle > 0 and app.getLabelBg('seq%sCurrent' % seq) != GUIConfig.appBgColor:
                    app.setLabelBg('seq%sCurrent' % seq, GUIConfig.appBgColor)
                label = Var.labels[seq]
                try:
                    meter_val = (delivered_block_cycles / total_expected_block_cycles) * 100
                    meter_val = 100.0 if meter_val > 100 else meter_val
                except ZeroDivisionError:
                    meter_val = 0.0
                meter_label = ('%s:     %s / %s' % (label, delivered_block_cycles,
                                                    int(total_expected_block_cycles)))
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
    now = datetime.datetime.now()
    Var.sched = []
    try:
        for time in Var.schedule.return_schedule(Var.kpi.d):
            if time:
                Var.sched.append(time)
    except AttributeError:
        pass
    var = 0
    for time in Var.sched:
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


def combine(time):
    return datetime.datetime.combine(datetime.date.today(), time)


def time_dif(time1, time2):
    timedif = (time2 - time1).total_seconds()
    timedif += 86400 if timedif < 0 else 0
    return timedif


app.registerEvent(counting)
app.setPollTime(200)

app.go()
