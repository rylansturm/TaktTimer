from app import app, schedule
from config import GUIVar, GUIConfig, basedir
import datetime
from math import floor
import os


class Var:
    now = datetime.datetime.now()
    mark = datetime.datetime.now()
    block = 0
    sched = schedule.Schedule("%s/schedules/%s.ini" % (os.path.dirname(__file__), 'Day'))
    started = False
    available_time = 23100
    demand = 360
    takt = 64.17
    tct = int(takt)
    tCycle = 0
    partsper = 2
    sequence_time = int(tct * partsper)
    parts_delivered = 0
    andon = False
    in_window = False
    early = 0
    late = 0
    on_time = 0
    lead_unverified = 0
    batting_avg = 0.0
    last_cycle = 0
    times_list = []


def counting():
    Var.now = datetime.datetime.now()
    Var.block = int(get_block_var() / 2) + 1 if get_block_var() % 2 != 0 else 0
    label_update()
    if Var.started and Var.block != 0:
        Var.tCycle = int(floor(Var.sequence_time - (Var.now - Var.mark).seconds))
        app.setLabel('tCycle', countdown_format(Var.tCycle))
    window = GUIVar.target_window * Var.partsper
    if Var.tCycle != GUIConfig.targetColor and -window <= Var.tCycle <= window:
        app.setLabelBg('tCycle', GUIConfig.targetColor)
    elif Var.tCycle != GUIConfig.andonColor and Var.tCycle < -window:
        app.setLabelBg('tCycle', GUIConfig.andonColor)
    elif Var.tCycle != GUIConfig.appBgColor and Var.tCycle > window:
        app.setLabelBg('tCycle', GUIConfig.appBgColor)


def cycle():
    Var.parts_delivered += Var.partsper
    t = Var.tCycle
    Var.last_cycle = Var.sequence_time - t
    Var.times_list.append(Var.last_cycle)
    app.setLabel('avgCycle', int(sum(Var.times_list) / len(Var.times_list)))
    display_cycle_times()
    window = GUIVar.target_window * Var.partsper
    if t > window:
        Var.early += 1
        Var.lead_unverified += 1
    elif t < -window:
        Var.late += 1
        Var.lead_unverified += 1
    else:
        Var.on_time += 1
    app.setLabel('TCT', countdown_format(get_tct()))
    app.setLabel('Seq', countdown_format(get_tct() * Var.partsper))
    Var.batting_avg = Var.on_time / sum([Var.on_time, Var.late, Var.early])
    Var.andon = False
    Var.mark = datetime.datetime.now()
    app.setMeter('partsOutMeter', (Var.parts_delivered/Var.demand) * 100,
                 '%s / %s Parts' % (Var.parts_delivered, Var.demand))


def display_cycle_times():
    cycle_list = []
    for i in Var.times_list:
        cycle_list.append(str(i))
    message = ', '.join(cycle_list)
    app.setMessage('cycleTimes', message)


def get_tct():
    remaining_time = Var.available_time - time_elapsed()
    remaining_demand = Var.demand - Var.parts_delivered
    if remaining_demand > 0:
        Var.tct = int(remaining_time / remaining_demand)
    else:
        Var.tct = int(Var.takt)
    behind, ahead = Var.tct < GUIVar.minimum_tct, Var.tct > int(Var.takt)
    Var.tct = GUIVar.minimum_tct if behind else int(Var.takt) if ahead else Var.tct
    return Var.tct


def label_update():
    app.setLabel('time', Var.now.strftime('%I:%M:%S %p'))
    app.setMeter('timeMeter', (time_elapsed()/Var.available_time) * 100,
                 '%s / %s' % (int(time_elapsed()), Var.available_time))
    app.setLabel('partsAhead', parts_ahead())
    app.setLabel('early', Var.early)
    app.setLabel('late', Var.late)
    app.setLabel('leadUnverified', Var.lead_unverified)
    app.setLabel('battingAVG', '%.3f' % Var.batting_avg)
    app.setLabel('lastCycle', Var.last_cycle)
    if get_block_var() in range(len(Var.sched.sched)):
        app.setLabel('nextBreak', Var.sched.sched[get_block_var()].strftime('%I:%M %p'))


def demand_set(btn):
    demand = int(app.getEntry('demand'))
    demand += (int(btn[:2]) if btn[2:4] == 'UP' else - int(btn[:2]))
    demand = (0 if demand < 0 else demand)
    app.setEntry('demand', demand)
    recalculate()


def partsper_set(btn):
    partsper = int(app.getEntry('partsper'))
    partsper += (int(btn[:2]) if btn[2:4] == 'UP' else - int(btn[:2]))
    partsper = (0 if partsper < 0 else partsper)
    app.setEntry('partsper', partsper)
    recalculate()


def get_block_var():
    """ returns the number of scheduled start AND stop times passed,
        '1' during first block, '2' during first break, '3' during block 2, etc. """
    time_list = Var.sched.sched
    passed = 0
    for time in time_list:
        if Var.now > time:
            passed += 1
    return passed


def time_elapsed():
    now = datetime.datetime.now()
    block = get_block_var()
    elapsed = (now - Var.sched.sched[0]).total_seconds()
    for i in range(int(len(Var.sched.sched)/2) - 1):
        elapsed -= (Var.sched.breakSeconds[i] if Var.block > i + 1 else 0)
    if block % 2 == 0:
        elapsed -= (now - Var.sched.sched[block - 1]).total_seconds()
    return elapsed


def parts_ahead():
    time = time_elapsed()
    expected = time / Var.takt
    return Var.parts_delivered - int(expected)


def press(btn):
    if btn == 'Go':
        for tab in GUIConfig.tabs:
            app.setTabbedFrameDisabledTab('Tabs', tab, disabled=False)
        app.setTabbedFrameSelectedTab('Tabs', 'Main')
        Var.mark = datetime.datetime.now()
        Var.started = True
        recalculate()
    if btn == 'leadUnverifiedButton':
        Var.lead_unverified = 0
        app.setLabel('leadUnverified', Var.lead_unverified)
    if btn == 'Set':
        Var.parts_delivered = int(app.getSpinBox('Parts Delivered'))
        app.setMeter('partsOutMeter', (Var.parts_delivered / Var.demand) * 100,
                     '%s / %s Parts' % (Var.parts_delivered, Var.demand))


def recalculate():
    Var.available_time = sum(Var.sched.blockSeconds)
    Var.demand = int(app.getEntry('demand'))
    Var.takt = Var.available_time / Var.demand
    Var.tct = get_tct()
    Var.partsper = int(app.getEntry('partsper'))
    Var.sequence_time = Var.tct * Var.partsper
    app.setLabel('Takt', countdown_format(int(Var.takt)))
    app.setLabel('takt2', countdown_format(int(Var.takt)))
    app.setLabel('TCT', countdown_format(get_tct()))
    app.setLabel('Seq', countdown_format(int(Var.sequence_time)))
    app.setMeter('partsOutMeter', (Var.parts_delivered / Var.demand) * 100,
                 '%s / %s Parts' % (Var.parts_delivered, Var.demand))


def key_press(key):
    if key == '1' or key == '<space>':
        cycle()


def menu_press(btn):
    """ handles all options under the File menu """
    if btn == 'Go Fullscreen':
        app.setSize('fullscreen')
    if btn == 'Exit Fullscreen':
        app.exitFullscreen()
    if btn == 'Exit':
        app.stop()


def enable_sched_select():
    for box in ['Shift: ', 'Schedule: ']:
        app.enableOptionBox(box)
    app.setOptionBox('Shift: ', shift_guesser())
    read_time_file()
    app.enableButton('Go')


def shift_guesser():
    return 'Grave' if Var.now.hour >= 23 else 'Swing' if Var.now.hour >= 15 \
        else 'Day' if Var.now.hour >= 7 else 'Grave'


def countdown_format(seconds: int):
    hours, minutes = divmod(seconds, 3600)
    minutes, seconds = divmod(minutes, 60)
    hour_label = '%s:%02d:%02d' % (hours, minutes, seconds)
    minute_label = '%s:%02d' % (minutes, seconds)
    second_label = ':%02d' % seconds
    return Var.tCycle if hours < 0 else hour_label if hours else minute_label if minutes else second_label


def read_time_file():
    file = basedir + '/%s/Schedules/%s/%s.ini' % (app.getOptionBox('Area: '),
                                                  app.getOptionBox('Shift: '),
                                                  app.getOptionBox('Schedule: '))
    try:
        Var.sched = schedule.Schedule(file)
    except KeyError:
        file = "%s/schedules/%s.ini" % (os.path.dirname(__file__), app.getOptionBox('Shift: '))
        Var.sched = schedule.Schedule(file)
    sched = Var.sched
    for block in range(1, 9):
        try:
            for label in ['block%sLabel' % block, 'block%s' % block,
                          'block%sTotal' % block, 'block%sPercent' % block]:
                app.removeLabel(label)
            print('removing block %s labels' % block)
        except:
            print('block %s does not exist. Ignoring command to delete labels.' % block)
    app.openLabelFrame('Parameters')
    start = datetime.datetime.time(sched.start).strftime('%I:%M%p')
    end = datetime.datetime.time(sched.end).strftime('%I:%M%p')
    percent = sum(sched.blockSeconds)/schedule.get_seconds(sched.start, sched.end)
    app.setLabel('start-end', '%s - %s' % (start, end))
    app.setLabel('start-endTotal', str(sum(sched.blockSeconds)) + ' seconds')
    app.setLabel('start-endPercent', ('%.2f%s of total time\n   spent in flow' % (percent, '%'))[2:])
    for block in range(1, len(sched.available) + 1):
        start = datetime.datetime.time(sched.available[block - 1])
        end = datetime.datetime.time(sched.breaks[block - 1])
        block_time = sched.blockSeconds[block-1]
        percent = block_time/sum(sched.blockSeconds)
        d = {'block%sLabel' % block:    ['%s Block: ' % GUIVar.ordinalList[block], 0, 0],
             'block%s' % block:         ['%s - %s' % (start.strftime('%I:%M%p'), end.strftime('%I:%M%p')), 0, 1],
             'block%sTotal' % block:    ['%s Seconds' % block_time, 1, 1],
             'block%sPercent' % block:  [('%.2f' % percent)[2:] + '% of available time', 1, 0]}
        x = 0
        for label in d:
            app.addLabel(label, d[label][0], block*3+d[label][1], d[label][2])
            x += 1
        for label in ['block%sTotal' % block, 'block%sPercent' % block]:
            app.getLabelWidget(label).config(font=GUIConfig.smallFont)
    app.stopLabelFrame()
    Var.mark = datetime.datetime.now()
