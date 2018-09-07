from app import app, timedata
from config import GUIVar, GUIConfig, basedir
import datetime
from math import floor
import os


class Var:
    now = datetime.datetime.now()
    mark = datetime.datetime.now()
    block = 0
    sched = timedata.TimeData("%s/schedules/%s.ini" % (os.path.dirname(__file__), 'Day'))
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
    Var.tct = get_tct()
    Var.sequence_time = Var.tct * Var.partsper
    app.setLabel('TCT', countdown_format(Var.tct))
    app.setLabel('Seq', countdown_format(Var.sequence_time))
    Var.batting_avg = Var.on_time / sum([Var.on_time, Var.late, Var.early])
    Var.andon = False
    Var.mark = datetime.datetime.now()
    app.setMeter('partsOutMeter', (Var.parts_delivered/Var.demand) * 100,
                 '%s / %s Parts' % (Var.parts_delivered, Var.demand))


def display_cycle_times():
    cycle_list = []
    for i in Var.times_list:
        cycle_list.append(str(i))
    data = ', '.join(cycle_list)
    app.setMessage('cycleTimes', data)


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
    demand = (1 if demand < 1 else demand)
    app.setEntry('demand', demand)
    recalculate()


def partsper_set(btn):
    partsper = int(app.getEntry('partsper'))
    partsper += (int(btn[:2]) if btn[2:4] == 'UP' else - int(btn[:2]))
    partsper = (1 if partsper < 1 else partsper)
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
        elapsed -= (Var.sched.breakSeconds[i] if block/2 >= i+1 else 0)
    if block % 2 == 0:
        elapsed -= (now - Var.sched.sched[block - 1]).total_seconds()
    return elapsed


def parts_ahead():
    time = time_elapsed()
    expected = time / Var.takt
    return Var.parts_delivered - int(expected)


def press(btn):
    if btn == 'Go':
        if int(app.getEntry('demand')) == 0:
            app.warningBox('No Demand', 'No demand was entered.')
        else:
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
    if key == '<F11>':
        app.exitFullscreen() if app.getFullscreen() else app.setFullscreen()


def menu_press(btn):
    """ handles all options under the File menu """
    if btn == 'Fullscreen':
        key_press('<F11>')
    if btn == 'Exit':
        app.stop()


def enable_sched_select():
    for box in ['Shift: ', 'Schedule: ']:
        app.enableOptionBox(box)
    app.setOptionBox('Shift: ', shift_guesser())
    read_time_file()
    app.enableButton('Go')


def enable_parts_out():
    if app.getCheckBox('Parts Out'):
        app.enableSpinBox('Parts Delivered')
        app.enableButton('Set')
    else:
        app.disableSpinBox('Parts Delivered')
        app.disableButton('Set')


def shift_guesser():
    return 'Grave' if Var.now.hour >= 23 else 'Swing' if Var.now.hour >= 15 \
        else 'Day' if Var.now.hour >= 7 else 'Grave'


def countdown_format(seconds: int):
    hours, minutes = divmod(seconds, 3600)
    minutes, seconds = divmod(minutes, 60)
    hour_label = '%s:%02d' % (hours, minutes)
    minute_label = '%s:%02d' % (minutes, seconds)
    second_label = ':%02d' % seconds
    return Var.tCycle if hours < 0 else hour_label if hours else minute_label if minutes else second_label


def shift_adjust(btn):
    block_index = int(btn[7:])-1
    change_list = Var.sched.available if btn[:5] == 'start' else Var.sched.breaks
    direction = btn[5:7]
    increment = GUIConfig.schedule_increment
    change_list[block_index] += increment if direction == 'UP' else -increment
    app.setLabel('block%s' % str(block_index+1), '%s -\n %s' % (Var.sched.available[block_index].strftime('%H:%M'),
                                                                Var.sched.breaks[block_index].strftime('%H:%M')))
    Var.sched.get_sched()
    Var.sched.get_block_seconds()
    Var.sched.get_break_seconds()
    app.setLabel('block%sTotal' % str(block_index+1), str(Var.sched.blockSeconds[block_index]) + ' Seconds')
    app.setLabel('start-endTotal', str(sum(Var.sched.blockSeconds)) + ' seconds')


def read_time_file():
    file = basedir + '/%s/Schedules/%s/%s.ini' % (app.getOptionBox('Area: '),
                                                  app.getOptionBox('Shift: '),
                                                  app.getOptionBox('Schedule: '))
    try:
        Var.sched = timedata.TimeData(file)
    except KeyError:
        file = "%s/schedules/%s.ini" % (os.path.dirname(__file__), app.getOptionBox('Shift: '))
        Var.sched = timedata.TimeData(file)
    sched = Var.sched
    for block in range(1, 9):
        try:
            for label in ['block%s' % block, 'block%sTotal' % block]:
                app.removeLabel(label)
            for button in ['startUP%s' % block, 'startDN%s' % block,
                           'endedUP%s' % block, 'endedDN%s' % block]:
                app.removeButton(button)
            app.removeLabelFrame('%s Block' % GUIVar.ordinalList[block])
            print('removing block %s labels' % block)
        except:
            print('block %s does not exist. Ignoring command to delete labels.' % block)
    app.openLabelFrame('Parameters')
    start = datetime.datetime.time(sched.start).strftime('%H:%M')
    end = datetime.datetime.time(sched.end).strftime('%H:%M')
    # percent = sum(sched.blockSeconds)/schedule.get_seconds(sched.start, sched.end)
    app.setLabel('start-end', '%s - %s' % (start, end))
    app.setLabel('start-endTotal', str(sum(sched.blockSeconds)) + ' seconds')
    # app.setLabel('start-endPercent', ('%.2f%s of total time\n   spent in flow' % (percent, '%'))[2:])
    for block in range(1, len(sched.available) + 1):
        with app.labelFrame('%s Block' % GUIVar.ordinalList[block], row=1, column=block-1):
            app.setSticky('new')
            app.setLabelFrameAnchor('%s Block' % GUIVar.ordinalList[block], 'n')
            start = datetime.datetime.time(sched.available[block-1])
            end = datetime.datetime.time(sched.breaks[block-1])
            block_time = sched.blockSeconds[block-1]
            # percent = block_time/sum(sched.blockSeconds)
            buttons = {'startUP%s' % block: [shift_adjust, 0, 2],
                       'startDN%s' % block: [shift_adjust, 0, 0],
                       'endedUP%s' % block: [shift_adjust, 1, 2],
                       'endedDN%s' % block: [shift_adjust, 1, 0],
                       }
            d = {'block%s' % block:         ['%s -\n %s' % (start.strftime('%H:%M'), end.strftime('%H:%M')), 0, 1, 2],
                 'block%sTotal' % block:    ['%s Seconds' % block_time, 2, 1, 0],
                 # 'block%sPercent' % block:  [('%.2f' % percent)[2:] + '% of available time', 2, 0]
                 }
            for label in d:
                app.addLabel(title=label, text=d[label][0], row=d[label][1], column=d[label][2], rowspan=d[label][3])
            for button in buttons:
                app.addButton(title=button, func=buttons[button][0],
                              row=buttons[button][1], column=buttons[button][2])
                app.setButton(button, '+' if button[5:7] == 'UP' else '-')

    app.stopLabelFrame()
    Var.mark = datetime.datetime.now()
