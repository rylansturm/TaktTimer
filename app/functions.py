from app import app, timedata
from config import GUIVar, GUIConfig, basedir
import configparser
import datetime
from math import floor
import os
from models import *


c = configparser.ConfigParser()
c.read('install.ini')


class Var:
    session = create_session()
    db_file = 'app.db'
    db_poll_count = 15
    time_open = datetime.datetime.now()
    now = datetime.datetime.now()
    mark = datetime.datetime.now()
    block = 0
    sched = timedata.TimeData()
    started = True
    available_time = sum(sched.blockSeconds)
    demand = 312
    shift = 'Day'
    takt = 74
    tct = int(takt)
    tCycle = 0
    partsper = int(c['Var']['partsper'])
    sequence_time = int(tct * partsper)
    parts_delivered = 0
    andon = False
    in_window = False
    early = 0
    late = 0
    on_time = 0
    hit = False
    lead_unverified = 0
    batting_avg = 0.0
    last_cycle = 0
    times_list = []
    seq = 1
    kpi = session.query(KPI).filter(KPI.d == datetime.date.today(),\
                                                KPI.shift == 'Day').first()
    kpi_id = None
    ahead = True
    schedule_edited = False
    schedule_option_list = []
    breaktime = True
    session.close()


def counting_worker():
    # print('Counting %s/50' % Var.db_poll_count)
    Var.now = datetime.datetime.now()
    Var.block = int(get_block_var() / 2) + 1 if get_block_var() % 2 != 0 else 0
    app.setLabel('block', Var.block)
    if not Var.breaktime and Var.block == 0:
        Var.breaktime = True
        break_seconds = Var.sched.breakSeconds[get_block_var() // 2]
        Var.mark += datetime.timedelta(seconds=break_seconds)
    elif Var.breaktime and Var.block != 0:
        Var.breaktime = False
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
    Var.db_poll_count += 1
    if Var.db_poll_count == 20:
        session = create_session()
        try:
            kpi = session.query(KPI).filter(KPI.shift == shift_guesser(),
                                            KPI.d == datetime.date.today()).one()
            if c['Install']['type'] == 'Worker':
                if Var.shift != kpi.shift or \
                        Var.sched.name != kpi.schedule.name or\
                        Var.demand != kpi.demand or\
                        Var.kpi_id != kpi.id or\
                        Var.available_time != kpi.schedule.available_time:
                    print(Var.available_time)
                    Var.shift = kpi.shift
                    read_time_file(shift=Var.shift, name=kpi.schedule.name)
                    Var.demand = kpi.demand
                    Var.kpi_id = kpi.id
                    Var.available_time = Var.sched.available_time
                    print(Var.available_time)
                    recalculate()
                    Var.started = True
        except:
            print("Today's KPI is not yet available")
        Var.db_poll_count = 0
        session.close()


def counting_server():
    app.setLabel('timestamp',
                 datetime.datetime.now().strftime("%a, %b %d, '%y\n    %I:%M:%S %p"))
    app.setEntry('demand', Var.demand)
    app.setLabel('totalTime', Var.available_time)
    if Var.kpi_id is None:
        session = create_session()
        try:
            Var.kpi = session.query(KPI).filter(KPI.d == datetime.date.today(),\
                                                KPI.shift == shift_guesser()).first()
            Var.kpi_id = Var.kpi.id
            Var.demand = Var.kpi.demand
            recalculate()
        except:
            Var.kpi = KPI(d=datetime.date.today(), shift=shift_guesser(),
                          demand=24, schedule=session.query(Schedule).filter(
                    Schedule.shift == shift_guesser(), Schedule.name == 'Regular').first())
            Var.demand = Var.kpi.demand
            session.add(Var.kpi)
            session.commit()
            Var.kpi_id = Var.kpi.id
            recalculate()
        Var.available_time = Var.kpi.schedule.available_time
        app.setOptionBox('Schedule: ', Var.kpi.schedule.name)
        session.close()


def cycle():
    Var.parts_delivered += Var.partsper
    t = Var.tCycle
    Var.last_cycle = Var.sequence_time - t
    Var.times_list.append(Var.last_cycle)
    app.setLabel('avgCycle', int(sum(Var.times_list) / len(Var.times_list)))
    display_cycle_times()
    window = GUIVar.target_window * Var.partsper
    if t > window:
        Var.hit = False
        Var.early += 1
        Var.lead_unverified += 1
    elif t < -window:
        Var.hit = False
        Var.late += 1
        Var.lead_unverified += 1
    else:
        Var.hit = True
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
    app.thread(data_log())


def data_log():
    session = create_session()
    new_cycle = Cycles(d=Var.mark, seq=Var.seq, cycle_time=Var.last_cycle,
                       parts_per=Var.partsper, delivered=Var.parts_delivered, hit=Var.hit)
    if Var.kpi_id:
        new_cycle.kpi_id = Var.kpi_id
    else:
        try:
            new_cycle.kpi_id = session.query(KPI).filter(KPI.d == datetime.date.today(),
                                                         KPI.shift == shift_guesser()).one().id
        except:
            pass
        Var.kpi = new_cycle.kpi
    session.add(new_cycle)
    session.commit()
    session.close()


def display_cycle_times():
    cycle_list = []
    for i in Var.times_list:
        cycle_list.append(str(i))
    data = ', '.join(cycle_list)
    app.clearTextArea('cycleTimes')
    app.setTextArea('cycleTimes', data)


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
        if Var.block == 0:
            app.setLabel('nextBreakLabel', 'Starting at: ')
        else:
            app.setLabel('nextBreakLabel', 'Next Break: ')
    if Var.ahead and int(app.getLabel('partsAhead')) < 0:
        Var.ahead = False
        app.setLabel('partsAheadLabel', 'Parts\nBehind')
        app.setLabelBg('partsAhead', 'red')
    if not Var.ahead and int(app.getLabel('partsAhead')) >= 0:
        Var.ahead = True
        app.setLabel('partsAheadLabel', 'Parts\nAhead')
        app.setLabelBg('partsAhead', GUIConfig.appBgColor)


def demand_set(btn):
    demand = int(app.getEntry('demand'))
    demand += (int(btn[:2]) if btn[2:4] == 'UP' else - int(btn[:2]))
    demand = (1 if demand < 1 else demand)
    session = create_session()
    kpi = Var.kpi
    kpi.demand = demand
    session.add(kpi)
    session.commit()
    session.close()
    Var.demand = demand
    app.setEntry('demand', demand)
    recalculate()


def partsper_set(btn):
    partsper = int(app.getEntry('partsper'))
    partsper += (int(btn[:2]) if btn[2:4] == 'UP' else - int(btn[:2]))
    partsper = (1 if partsper < 1 else partsper)
    app.setEntry('partsper', partsper)
    Var.partsper = partsper
    c['Var']['partsper'] = str(partsper)
    with open('install.ini', 'w') as configfile:
        c.write(configfile)
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
        elapsed -= (Var.sched.breakSeconds[i] if block/2 > i+1 else 0)
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
            if c['Install']['type'] == 'Server':
                session = create_session()
                try:
                    kpi = session.query(KPI).filter(KPI.shift == app.getOptionBox('Shift: '),
                                                    KPI.d == datetime.date.today()).one()
                except:
                    kpi = KPI(d=datetime.date.today(), shift=app.getOptionBox('Shift: '))
                kpi.demand = app.getEntry('demand')
                kpi.schedule_id = Var.sched.id
                session.add(kpi)
                session.commit()
                session.close()
    if btn == 'leadUnverifiedButton':
        Var.lead_unverified = 0
        app.setLabel('leadUnverified', Var.lead_unverified)
    if btn == 'Set':
        Var.parts_delivered = int(app.getSpinBox('Parts Delivered'))
        app.setMeter('partsOutMeter', (Var.parts_delivered / Var.demand) * 100,
                     '%s / %s Parts' % (Var.parts_delivered, Var.demand))


def recalculate():
    print('app.functions.recalculate')
    Var.available_time = sum(Var.sched.blockSeconds)
    # Var.demand = int(app.getEntry('demand'))
    Var.takt = Var.available_time / Var.demand
    Var.tct = get_tct()
    try:
        # Var.partsper = int(app.getEntry('partsper'))
        Var.sequence_time = Var.tct * Var.partsper
        app.setLabel('Takt', countdown_format(int(Var.takt)))
        app.setLabel('TCT', countdown_format(Var.tct))
        app.setLabel('Seq', countdown_format(int(Var.sequence_time)))
        app.setMeter('partsOutMeter', (Var.parts_delivered / Var.demand) * 100,
                     '%s / %s Parts' % (Var.parts_delivered, Var.demand))
    except Exception:
        print('skipping certain labels belonging to Worker')
    try:
        app.setLabel('takt2', countdown_format(int(Var.takt)))
        app.setEntry('demand', Var.demand)
    except Exception:
        print('skipping certain labels belonging to Server')


def key_press(key):
    if key == '1' or key == '<space>':
        cycle()
    if key == '<F11>':
        app.exitFullscreen() if app.getFullscreen() else app.setFullscreen()


def menu_press(btn):
    """ handles all options under the File menu """
    if btn == 'Fullscreen':
        key_press('<F11>')
    elif btn == 'Exit':
        app.stop()
    else:
        Var.seq = int(btn)
        app.setLabel('sequence_number', Var.seq)


# def enable_sched_select():
#     for box in ['Shift: ', 'Schedule: ']:
#         app.enableOptionBox(box)
#     app.setOptionBox('Shift: ', shift_guesser())
#     session = create_session(Var.db_file)
#     schedule_list = []
#     for sched in session.query(Schedule).filter(Schedule.shift == shift_guesser()).all():
#         schedule_list.append(sched.name)
#     app.changeOptionBox('Schedule: ', schedule_list)
#     read_time_file()
#     app.enableButton('Go')


def enable_parts_out():
    if app.getCheckBox('Parts Out'):
        app.enableSpinBox('Parts Delivered')
        app.enableButton('Set')
    else:
        app.disableSpinBox('Parts Delivered')
        app.disableButton('Set')


def shift_guesser():
    return 'Grave' if Var.now.hour >= 18 else 'Swing' if Var.now.hour >= 15 \
        else 'Day' if Var.now.hour >= 7 else 'Grave'


Var.shift = shift_guesser()


def countdown_format(seconds: int):
    hours, minutes = divmod(seconds, 3600)
    minutes, seconds = divmod(minutes, 60)
    hour_label = '%s:%02d' % (hours, minutes)
    minute_label = '%s:%02d' % (minutes, seconds)
    second_label = ':%02d' % seconds
    return Var.tCycle if hours < 0 else hour_label if hours else minute_label if minutes else second_label


def shift_adjust(btn):
    Var.schedule_edited = True
    app.setOptionBox('Schedule: ', 'Custom', callFunction=False)
    session = create_session()
    old_schedule = session.query(Schedule).filter(Schedule.id == Var.sched.id).first()
    try:
        new_schedule = session.query(Schedule).filter(Schedule.shift == app.getOptionBox('Shift: '),
                                                      Schedule.name == 'Custom').one()
    except:
        new_schedule = Schedule(name='Custom', shift=app.getOptionBox('Shift: '))
    new_schedule.get_times(*old_schedule.return_times())
    e = len(btn)
    block = int(btn[e-1])
    change_list = new_schedule.return_times()
    direction = btn[e-3:e-1]
    index = (2 * (block - 1)) if btn[:e-3] == 'start' else ((2 * block) - 1)
    increment = GUIConfig.schedule_increment
    for b in range(1, 9):
        if b == block:
            old_time = change_list[index]
            exec('new_schedule.' + btn[:e-3] + btn[e-1] + " = datetime.datetime.time(datetime.datetime.combine"
                                                          "(datetime.date.today(), old_time)"
                                                          " + (increment if direction == 'UP' else -increment))")
    new_schedule.get_available_time()
    session.add(new_schedule)
    kpi = session.query(KPI).filter(KPI.d == datetime.date.today(),
                                    KPI.shift == shift_guesser()).one()
    kpi.schedule = new_schedule
    Var.kpi = kpi
    session.add(kpi)
    session.commit()
    session.close()
    read_time_file(shift=shift_guesser(), name='Custom')
    app.setLabel('block%s' % block, '%s\n%s' % (Var.sched.available[block-1].strftime('%I:%M %p'),
                                                Var.sched.breaks[block-1].strftime('%I:%M %p')))
    Var.sched.get_sched()
    Var.sched.get_block_seconds()
    Var.sched.get_break_seconds()
    app.setLabel('block%sTotal' % str(block), str(Var.sched.blockSeconds[block-1]) + '\nSeconds')
    Var.available_time = sum(Var.sched.blockSeconds)
    Var.takt = int(Var.available_time / Var.demand)
    app.setLabel('totalTime', Var.available_time)
    app.setLabel('takt2', countdown_format(Var.takt))


def set_kpi(btn):
    if int(app.getEntry('demand')) == 0:
        app.warningBox('No Demand', 'No demand was entered.')
    else:
        if Var.schedule_edited:
            app.showSubWindow('New Schedule')
        else:
            Var.mark = datetime.datetime.now()
            recalculate()
        session = create_session()
        try:
            kpi = session.query(KPI).filter(KPI.shift == app.getOptionBox('Shift: '),
                                            KPI.d == datetime.date.today()).one()
        except:
            kpi = KPI(d=datetime.date.today(), shift=app.getOptionBox('Shift: '))
        kpi.demand = app.getEntry('demand')
        kpi.schedule_id = Var.sched.id
        session.add(kpi)
        session.commit()
        session.close()


def change_schedule_box_options():
    Var.schedule_edited = False
    session = create_session()
    options = session.query(Schedule).filter(Schedule.shift == app.getOptionBox('Shift: '))
    Var.schedule_option_list = []
    for sched in options:
        Var.schedule_option_list.append(sched.name)
    if 'Custom' not in Var.schedule_option_list:
        Var.schedule_option_list.append('Custom')
    app.changeOptionBox('Schedule: ', Var.schedule_option_list)
    session.close()


def determine_time_file():
    sched = app.getOptionBox('Schedule: ')
    shift = app.getOptionBox('Shift: ')
    read_time_file()
    Var.schedule_edited = False
    session = create_session()
    kpi = session.query(KPI).filter(KPI.d == datetime.date.today(),
                                    KPI.shift == shift).one()
    kpi.schedule = session.query(Schedule).filter(Schedule.name == sched, Schedule.shift == shift).one()
    session.add(kpi)
    session.commit()
    session.close()


def read_time_file(shift=None, name=None):
    if shift is None:
        shift = app.getOptionBox('Shift: ')
    if name is None:
        name = app.getOptionBox('Schedule: ')
    print('reading time file')
    # file = basedir + '/%s/Schedules/%s/%s.ini' % (app.getOptionBox('Area: '),
    #                                               app.getOptionBox('Shift: '),
    #                                               app.getOptionBox('Schedule: '))
    try:
        Var.sched = timedata.TimeData(shift=shift, name=name)
#        schedule_list = []
#        session = create_session('app.db')
#        for sched in session.query(Schedule).filter(Schedule.shift == app.getOptionBox('Shift: ')).all():
#            schedule_list.append(sched.name)
#        app.changeOptionBox('Schedule: ', schedule_list, callFunction=False)
    except KeyError:
        file = "%s/schedules/%s.ini" % (os.path.dirname(__file__), app.getOptionBox('Shift: '))
        Var.sched = timedata.TimeData(file)
    print('created %s' % Var.sched)
    sched = Var.sched
    print('removing old block data')
    for block in range(1, 9):
        try:
            for label in ['block%s' % block, 'block%sTotal' % block]:
                app.removeLabel(label)
            for button in ['startUP%s' % block, 'startDN%s' % block,
                           'endUP%s' % block, 'endDN%s' % block]:
                app.removeButton(button)
            app.removeLabelFrame('%s Block' % GUIVar.ordinalList[block])
            print('removing block %s labels' % block)
        except:
            print('block %s does not exist. Ignoring command to delete labels.' % block)
    app.openFrame('Parameters')
    # start = datetime.datetime.time(sched.start).strftime('%H:%M')
    # end = datetime.datetime.time(sched.end).strftime('%H:%M')
    # percent = sum(sched.blockSeconds)/schedule.get_seconds(sched.start, sched.end)
    # app.setLabel('start-end', '%s - %s' % (start, end))
    # app.setLabel('start-endTotal', str(sum(sched.blockSeconds)) + ' seconds')
    # app.setLabel('start-endPercent', ('%.2f%s of total time\n   spent in flow' % (percent, '%'))[2:])
    print('creating new block data')
    for block in range(1, len(sched.available) + 1):
        with app.frame('%s Block' % GUIVar.ordinalList[block], row=block-1, column=0):
            app.setSticky('new')
            start = datetime.datetime.time(sched.available[block-1])
            end = datetime.datetime.time(sched.breaks[block-1])
            block_time = sched.blockSeconds[block-1]
            # percent = block_time/sum(sched.blockSeconds)
            buttons = {'startUP%s' % block: [shift_adjust, 0, 2],
                       'startDN%s' % block: [shift_adjust, 0, 0],
                       'endUP%s' % block: [shift_adjust, 1, 2],
                       'endDN%s' % block: [shift_adjust, 1, 0],
                       }
            d = {'block%s' % block:         ['%s\n%s' % (start.strftime('%I:%M %p'), end.strftime('%I:%M %p')), 0, 1, 2],
                 'block%sTotal' % block:    ['%s\nSeconds' % block_time, 0, 3, 2],
                 # 'block%sPercent' % block:  [('%.2f' % percent)[2:] + '% of available time', 2, 0]
                 }
            for label in d:
                app.addLabel(title=label, text=d[label][0], row=d[label][1], column=d[label][2], rowspan=d[label][3])
            if c['Install']['type'] == 'Server':
                for button in buttons:
                    e = len(button)
                    app.addButton(title=button, func=buttons[button][0],
                                  row=buttons[button][1], column=buttons[button][2])
                    app.setButton(button, '+' if button[e-3:e-1] == 'UP' else '-')
    app.stopFrame()
    Var.mark = datetime.datetime.now()
    print('finished with app.function.read_time_file')
