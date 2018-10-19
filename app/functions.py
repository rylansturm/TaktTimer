from app import app, timedata
from config import *
import configparser
from math import floor
import os
from models import *
from appJar.appjar import ItemLookupError
from sqlalchemy.orm.exc import NoResultFound
if GUIConfig.platform == 'linux':
    from app.lights import *


c = configparser.ConfigParser()
c.read('install.ini')


class Var:
    """ Variables used in each app instance, constantly changing """
    session = create_session()                  # db session
    db_poll_count = 95                          # auto increments and polls db at db_poll_value
    db_poll_target = 100                        # recurrence of db poll
    time_open = datetime.datetime.now()         # value written at app start
    now = datetime.datetime.now()               # auto updates with counting function
    mark = datetime.datetime.now()              # datetime at most recent cycle
    block = 0                                   # current block
    sched = timedata.TimeData()                 # TODO: remove timedata objects and replace w/db
    started = False                             # fixes abnormal timer countdown at start of shift
    available_time = sum(sched.blockSeconds)    # total available time for shift
    demand = 312                                # part demand (total including rejects
    shift = 'Day'                               # current shift
    takt = 74.0                                 # takt time (float for accurate calculations, displays as int)
    tct = int(takt)                             # target cycle time ("remaining takt time")
    using_tct = True                            # whether or not we are using a fluctuating tct
    tCycle = 0                                  # current countdown value
    partsper = int(c['Var']['partsper'])        # parts delivered per cycle
    sequence_time = int(tct * partsper)         # tct * partsper, when the sequence is expected to deliver
    parts_delivered = 0                         # total parts delivered
    early = 0                                   # number of cycles completed before target window
    late = 0                                    # number of cycles completed after target window
    on_time = 0                                 # number of cycles completed in target window
    hit = False                                 # whether the last cycle was on target, used for DB entry
    batting_avg = 0.0                           # average of cycles completed in target window
    last_cycle = 0                              # the cycle time of the most recent cycle
    times_list = []                             # complete list of each cycle time for current shift by this sequence
    seq = int(c['Var']['seq'])                  # numerical representation for each operator (from start to end of flow)
    kpi = session.query(KPI).filter(KPI.d == datetime.date.today(),
                                    KPI.shift == 'Day').first()     # db entry for current shift (demand, schedule)
    kpi_id = None                               # id for simpler db queries
    ahead = True                                # whether or not we are currently ahead of pace
    schedule_edited = False                     # whether TL has adjusted schedule (shows 'Custom' for schedule)
    schedule_option_list = []                   # replaces GUIVar.scheduleTypes with list of schedules from db
    breaktime = True                            # whether it is currently break (fixes countdown issues after break)
    rejects = 0                                 # number of parts rejected from sequence
    andon = False                               # whether the operator has pushed the andon button
    unresponded = 0                             # number of Takt Time andons not responded to by TL
    andonCount = 0                              # total number of times operator has hit andon button
    andonCountMsg = '0'                         # for the TMAndon label, normally '%s + %s' % (andonCount, unresponded)
    new_shift = True                            # prevents multiple calls on reset() at the shift change
    session.close()


def counting_worker():
    """ registered event for GUI instance of type: Worker; runs about 10 times/second"""
    app.setLabel('timestamp', datetime.datetime.now().strftime("%a, %b %d, '%y\n    %I:%M:%S %p"))
    Var.now = datetime.datetime.now()
    Var.block = int(get_block_var() / 2) + 1 if get_block_var() % 2 != 0 else 0

    """ Setting the mark when the first block happens """
    if Var.block != 0:  # if we are currently running:
        if not Var.started:  # if we haven't already started the shift on this timer:
            Var.started = True  # well now we have
            Var.mark = Var.now  # let's start the counter from here rather than whenever the timer turned on
            recalculate()
    app.setLabel('block', 'Block ' + str(Var.block) if Var.block != 0 else 'Break')

    """ stop the timer from subtracting the break times when we start back up """
    if not Var.breaktime and Var.block == 0:  # when we first go to break
        Var.breaktime = True  # make sure the function isn't called again
        if 0 < get_block_var() < len(Var.sched.sched):  # don't try to add a break value at the end of the shift
            break_seconds = Var.sched.breakSeconds[(get_block_var() // 2) - 1]  # how many seconds for this break?
            Var.mark += datetime.timedelta(seconds=break_seconds)  # push the mark forward
    elif Var.breaktime and Var.block != 0:  # when available time starts again:
        Var.breaktime = False  # reset this variable

    label_update()  # separate function for readability

    """ update the main counter """
    if Var.started and Var.block != 0:  # if we are in 'available time'
        Var.tCycle = int(floor(Var.sequence_time - (Var.now - Var.mark).seconds))  # expected_time - time_since_mark
        app.setLabel('tCycle', countdown_format(Var.tCycle))  # countdown_format just makes it look better
    else:
        app.setLabel('tCycle', 'BRK')

    """ control the andon tower lights """
    if GUIConfig.platform == 'linux':
        run_lights()

    """ set the tCycle label background as a visual cue """
    window = GUIVar.target_window * Var.partsper  # the acceptable window for stable sequences
    color = app.getLabelBg('tCycle')  # what color is it right now?
    if Var.block != 0:  # if we are in 'available time'
        if color != GUIConfig.targetColor and -window <= Var.tCycle <= window:  # if in the window and not right color:
            app.setLabelBg('tCycle', GUIConfig.targetColor)  # Let the operator know now is a good time
        elif color != GUIConfig.andonColor and Var.tCycle < -window:  # if late and not the right color:
            app.setLabelBg('tCycle', GUIConfig.andonColor)  # Let the operator know they failed (... I mean systems?)
        elif color != GUIConfig.appBgColor and Var.tCycle > window:  # if not yet in the window and not the right color:
            app.setLabelBg('tCycle', GUIConfig.appBgColor)  # Stop letting the operator know so much. Just chill.
    else:
        if color != GUIConfig.break_color:
            app.setLabelBg('tCycle', GUIConfig.break_color)

    """ check to see if we are reading the right KPI """
    Var.db_poll_count += 1  # auto-increment and check every db_poll_target-th time. No need to check too frequently
    if Var.db_poll_count == Var.db_poll_target:  # every db_poll_target-th time
        session = create_session()
        try:  # there should one (only one) kpi that matches. If not, go to the exception.
            if shift_guesser() == 'Grave' and Var.now < Var.sched.sched[-1]:
                date = datetime.date.today() - datetime.timedelta(days=1)
            else:
                date = datetime.date.today()
            kpi = session.query(KPI).filter(KPI.shift == shift_guesser(),
                                            KPI.d == date).one()  # the kpi for today, this shift
            seq = session.query(Cycles.seq).filter(Cycles.kpi == kpi).all()  # all the active sequences on this kpi
            """ if the info we have does not match what's on the kpi, update the kpi """
            if Var.shift != kpi.shift or \
                    Var.sched.name != kpi.schedule.name or\
                    Var.demand != kpi.demand or\
                    Var.kpi_id != kpi.id or\
                    Var.available_time != kpi.schedule.available_time:
                print('shifts:')
                print(Var.shift)
                print(kpi.shift)
                print()
                print('sched.name')
                print(Var.sched.name)
                print(kpi.schedule.name)
                print()
                print('kpi_id')
                print(Var.kpi_id)
                print(kpi.id)
                print()
                print('available time')
                print(Var.available_time)
                print(kpi.schedule.available_time)
                Var.new_shift = False
                Var.shift = kpi.shift
                read_time_file(shift=Var.shift, name=kpi.schedule.name)  # creates timedata.TimeData object as Var.sched
                Var.demand = kpi.demand
                Var.kpi_id = kpi.id
                Var.available_time = Var.sched.available_time
                recalculate()  # resets takt, tct, seq_time, and related labels
                app.setLabel('Schedule: ', Var.sched.name + ' Schedule')
                if (Var.seq, ) in seq:
                    Var.parts_delivered = session.query(Cycles.delivered).filter(
                        Cycles.kpi == kpi, Cycles.seq == Var.seq).order_by(
                        Cycles.d.desc()).first().delivered
                    app.setMeter('partsOutMeter', (Var.parts_delivered / Var.demand) * 100,
                                 '%s / %s Parts' % (Var.parts_delivered, Var.demand))
        except NoResultFound:
            print("Either no KPI exists for the current time, or a duplicate was made.")
        Var.db_poll_count = 0
        session.close()


def counting_server():
    """ registered event for GUI instance of type: [Server, Team Lead]; runs about 5 times/second"""
    Var.now = datetime.datetime.now()
    app.setLabel('timestamp',
                 Var.now.strftime("%a, %b %d, '%y\n    %I:%M:%S %p"))
    if Var.kpi_id is None:  # if we haven't made a connection to the kpi yet:
        print('no kpi, getting one now')
        session = create_session()
        try:  # try to get the existing kpi, don't make one unless there isn't one already
            Var.kpi = session.query(KPI).filter(KPI.d == datetime.date.today(),
                                                KPI.shift == shift_guesser()).one()
            Var.kpi_id = Var.kpi.id
            Var.demand = Var.kpi.demand
            recalculate()
        except NoResultFound:  # make one if you didn't find one
            if app.yesNoBox('New Shift?', 'Create plan for current shift?'):
                Var.kpi = KPI(d=datetime.date.today(), shift=shift_guesser(),
                              demand=Var.demand, schedule=session.query(Schedule).filter(
                        Schedule.shift == shift_guesser(), Schedule.name == 'Regular').first())
                Var.demand = Var.kpi.demand
                session.add(Var.kpi)
                session.commit()
                Var.kpi_id = Var.kpi.id
                recalculate()
        Var.available_time = Var.kpi.schedule.available_time
        app.setOptionBox('Schedule: ', Var.kpi.schedule.name)
        session.close()
    app.setEntry('demand', Var.demand)
    app.setLabel('totalTime', Var.available_time)
    if Var.now > Var.sched.end_of_shift:
        Var.shift = shift_guesser()
        app.setOptionBox('Shift: ', Var.shift)
        app.setOptionBox('Schedule: ', 'Regular')
        reset()


def andon():
    """ gives operator option to manually turn on red andon light for non takt-related andons """
    Var.andon = True
    Var.unresponded += 1
    app.setButtonBg('TMAndonButton', GUIConfig.andonColor)


def run_lights():
    """ controls the andon lights. called in counting_worker """
    window = GUIVar.target_window * Var.partsper  # the acceptable window for stable sequences

    if Var.block == 0:  # do nothing on breaks
        Light.set_all(0, 0, 0)
    elif Var.tCycle <= GUIVar.buzzer_time_out:  # stop buzzing after so many seconds, but keep red light on
        Light.set_all(1, 0, 0)
    else:
        """ normal functioning during available time """

        """ control red light """
        if Var.andon:  # if the operator manually signals the andon by pressing the tCycle label
            if Var.now.second % 2 == 0:  # blink the red light
                Light.red(True)
            else:
                Light.red(False)
        else:  # otherwise only turn the red light on when TT is missed
            if Var.tCycle < -window:
                Light.red(True)
            else:
                Light.red(False)

        """ control the green light """
        if Var.tCycle > window:  # green is on when we haven't missed TT
            Light.green(True)
        elif -window <= Var.tCycle <= window:  # green flashes when in the target window
            if Var.now.second % 2 == 0:
                Light.green(True)
            else:
                Light.green(False)
        else:
            Light.green(False)

        """ control buzzer """
        if -window - 1 <= Var.tCycle < -window:  # buzzer is on for one second when TT missed
            Light.buzzer(True)
        if Var.tCycle < -window and Var.tCycle % 60 == 0:  # buzzer repeats once per minute when TT missed
            Light.buzzer(True)
        else:  # otherwise keep the buzzer off
            Light.buzzer(False)


def cycle():
    """ This is what happens when the button is pushed each cycle by the operators """
    if Var.tCycle < Var.sequence_time - GUIVar.cycle_time_out:  # helps avoid accidental button presses
        Var.parts_delivered += Var.partsper  # add parts to the delivered quantity
        t = Var.tCycle  # what did the timer read when we cycled?
        Var.last_cycle = Var.sequence_time - t
        Var.times_list.append(Var.last_cycle)
        app.setLabel('avgCycle', int(sum(Var.times_list) / len(Var.times_list)))
        display_cycle_times()

        """ was the part delivered late, early, on time? """
        window = GUIVar.target_window * Var.partsper
        if t > window:
            Var.hit = False
            Var.early += 1
        elif t < -window:
            Var.hit = False
            Var.late += 1
        else:
            Var.hit = True
            Var.on_time += 1

        Var.tct = get_tct()
        Var.sequence_time = Var.tct * Var.partsper
        Var.tCycle = Var.sequence_time
        app.setLabel('tCycle', countdown_format(Var.tCycle))
        app.setLabelBg('tCycle', GUIConfig.appBgColor)
        app.setLabel('TCT', countdown_format(Var.tct))
        app.setLabel('Seq', countdown_format(Var.sequence_time))
        Var.batting_avg = Var.on_time / sum([Var.on_time, Var.late, Var.early])
        Var.mark = datetime.datetime.now()
        yields = (Var.parts_delivered - Var.rejects) / Var.parts_delivered
        app.setButton('Reject + 1', 'Reject + 1\nRejects: %s\nYields: %.02f' % (Var.rejects, yields))
        app.setMeter('partsOutMeter', (Var.parts_delivered/Var.demand) * 100,
                     '%s / %s Parts' % (Var.parts_delivered - Var.rejects, Var.demand - Var.rejects))
        app.thread(data_log())  # save it! but don't make me wait on you.


def data_log():
    """ where data goes to die I mean be analyzed """
    session = create_session()
    new_cycle = Cycles(d=Var.mark, seq=Var.seq, cycle_time=Var.last_cycle,
                       parts_per=Var.partsper, delivered=Var.parts_delivered, hit=Var.hit)
    if Var.kpi_id:
        new_cycle.kpi_id = Var.kpi_id
    else:
        try:
            new_cycle.kpi_id = session.query(KPI).filter(KPI.d == datetime.date.today(),
                                                         KPI.shift == shift_guesser()).one().id
        except NoResultFound:
            pass
        Var.kpi = new_cycle.kpi
    session.add(new_cycle)
    session.commit()
    session.close()


def display_cycle_times():
    """ updates the text area on the Data tab to show every cycle time this shift """
    cycle_list = []
    for i in Var.times_list:
        cycle_list.append(str(i))
    data = ', '.join(cycle_list)
    app.clearTextArea('cycleTimes')
    app.setTextArea('cycleTimes', data)


def get_tct():
    """ returns 'remaining takt time', or remaining_time//remaining_demand """
    remaining_time = Var.available_time - time_elapsed()
    remaining_demand = Var.demand - Var.parts_delivered
    if remaining_demand > 0:
        Var.tct = int(remaining_time / remaining_demand)
    else:
        Var.tct = int(Var.takt)
    """ Don't go higher than original Takt Time, don't go lower than GUIVar.minimum_tct """
    behind, ahead = Var.tct < GUIVar.minimum_tct, Var.tct > int(Var.takt)
    Var.tct = GUIVar.minimum_tct if behind else int(Var.takt) if ahead else Var.tct
    return Var.tct if Var.using_tct else int(Var.takt)


def use_tct():
    """ changes whether or not we are using the fluctuating TCT  ## Currently only locally set ## """
    # TODO: make this a db column on KPI table so the TL can set it globally
    Var.using_tct = not Var.using_tct
    if Var.using_tct:
        app.setLabelBg('TCTLabel', GUIConfig.appBgColor)
        app.setLabelBg('TCT', GUIConfig.appBgColor)
    else:
        app.setLabelBg('TCTLabel', 'dark grey')
        app.setLabelBg('TCT', 'dark grey')
    recalculate()


def label_update():
    """ updates the majority of labels throughout GUI, called from counting function """
    app.setLabel('time', Var.now.strftime('%I:%M:%S %p'))
    app.setMeter('timeMeter', (time_elapsed()/Var.available_time) * 100,
                 '%s / %s' % (int(time_elapsed()), Var.available_time))
    disparity = parts_ahead() if parts_ahead() >= 0 else -(parts_ahead())
    app.setLabel('partsAhead', disparity)
    app.setLabel('partsOut', Var.parts_delivered)
    app.setLabel('early', Var.early)
    app.setLabel('late', Var.late)
    app.setLabel('battingAVG', '%.3f' % Var.batting_avg)
    app.setLabel('lastCycle', Var.last_cycle)
    app.setMeter('partsOutMeter', (Var.parts_delivered / Var.demand) * 100,
                 '%s / %s Parts' % (Var.parts_delivered - Var.rejects, Var.demand - Var.rejects))

    """ sets TM andon label """
    if Var.andon:
        Var.andonCountMsg = '%s + %s' % (Var.andonCount, Var.unresponded)
    else:
        Var.andonCountMsg = Var.andonCount
    app.setLabel('TMAndon', Var.andonCountMsg)

    """ set the label for 'Next Break' or 'Starting at' depending on where we are """
    if get_block_var() in range(len(Var.sched.sched)):
        app.setLabel('nextBreak', Var.sched.sched[get_block_var()].strftime('%I:%M %p'))
        if Var.block == 0:
            app.setLabel('nextBreakLabel', 'Starting at: ')
        else:
            app.setLabel('nextBreakLabel', 'Next Break: ')

    """ set the partsAhead label color and text ('ahead' or 'behind') """
    if Var.ahead and parts_ahead() < 0:
        Var.ahead = False
        app.setLabel('partsAheadLabel', 'Parts\nBehind')
        app.setLabelBg('partsAhead', 'red')
    if not Var.ahead and parts_ahead() >= 0:
        Var.ahead = True
        app.setLabel('partsAheadLabel', 'Parts\nAhead')
        app.setLabelBg('partsAhead', GUIConfig.appBgColor)


def demand_set(btn):
    """ Sets the demand and saves it to the KPI. Done from the TL computer """
    demand = int(app.getEntry('demand'))  # start from where it is now
    demand += (int(btn[:2]) if btn[2:4] == 'UP' else - int(btn[:2]))  # go up or down this interval
    demand = (1 if demand < 1 else demand)  # Demand won't go below 1
    session = create_session()  # Save it!
    kpi = Var.kpi               #
    kpi.demand = demand         #
    session.add(kpi)            #
    session.commit()            #
    session.close()             #
    Var.demand = demand         # set global(ish) variable
    app.setEntry('demand', demand)  # oh yeah, write it back up there.
    recalculate()  # reset values for TT, TCT, Seq time, etc


def partsper_set(btn):
    """ sets the parts delivered per cycle from each worker computer """
    partsper = int(app.getLabel('partsper'))  # start from where it is now
    partsper += (int(btn[:2]) if btn[2:4] == 'UP' else - int(btn[:2]))  # go up or down this interval
    partsper = (1 if partsper < 1 else partsper)  # partsper won't go below 1
    app.setLabel('partsper', partsper)  # write it on the gui
    Var.partsper = partsper  # set global(ish) variable
    c['Var']['partsper'] = str(partsper)            # Save it!
    with open('install.ini', 'w') as configfile:    #
        c.write(configfile)                         #
    recalculate()  # reset values for sequence time, which is based on tct and partsper


def parts_out_set(btn):
    """ sets the total parts delivered on this computer """
    parts = Var.parts_delivered  # start from where it is now
    parts += (int(btn[:2]) if btn[2:4] == 'UP' else - int(btn[:2]))  # go up or down this interval
    parts = 0 if parts < 0 else parts  # parts won't go below 0
    Var.parts_delivered = parts  # reset global(ish) variable
    app.setLabel('partsOut', Var.parts_delivered)  # write in on the gui
    app.setMeter('partsOutMeter', (Var.parts_delivered / Var.demand) * 100,
                 '%s / %s Parts' % (Var.parts_delivered - Var.rejects, Var.demand - Var.rejects))


def get_block_var():
    """ returns the number of scheduled start AND stop times passed,
        '1' during first block, '2' during first break, '3' during block 2, etc. """
    time_list = Var.sched.sched
    passed = 0
    if shift_guesser() == 'Grave':  # Grave crosses a date change, so is handled differently
        if Var.now > time_list[0]:
            return 1
        else:
            passed = 1
            for time in time_list[1:]:
                if Var.now > time:
                    passed += 1
    else:  # for Day and Swing
        """ iterate through each time in the schedule, and increment the 'passed' variable if the time has passed """
        for time in time_list:
            if Var.now > time:
                passed += 1
    """ at the end of the shift, run the reset function """
    if passed == len(time_list):
        if not Var.new_shift:
            if app.yesNoBox('New Shift?', 'Start the next shift?'):
                reset()
    return passed


def reset():
    """ reset all necessary variables for the incoming shift """
    Var.parts_delivered = 0
    Var.early = 0
    Var.late = 0
    Var.on_time = 0
    Var.unresponded = 0
    Var.batting_avg = 0
    Var.times_list = []
    Var.started = False
    Var.tCycle = 0
    Var.rejects = 0
    Var.andon = False
    Var.unresponded = 0
    Var.andonCount = 0
    Var.andonCountMsg = '0'
    Var.kpi_id = None
    Var.new_shift = True


def time_elapsed():
    """ returns the amount of 'available time' that has passed as float """
    now = datetime.datetime.now()
    block = get_block_var()
    elapsed = (now - Var.sched.sched[0]).total_seconds()  # total time since start
    for i in range(int(len(Var.sched.sched)/2) - 1):  # subtract each break that is already completely passed
        elapsed -= (Var.sched.breakSeconds[i] if block/2 > i+1 else 0)
    if block % 2 == 0:  # if its currently break, just keep subtracting however long it has been break
        elapsed -= (now - Var.sched.sched[block - 1]).total_seconds()
    elapsed += (86400 if elapsed < 0 else 0)
    return elapsed


def parts_ahead():
    """ returns the difference between where we should be and where we are """
    time = time_elapsed()
    expected = time / Var.takt
    return Var.parts_delivered - int(expected)


def press(btn):
    """ handles non-specific button pushes """

    """ reset lead_unverified counter to 0 and turn off blinking andon light """
    if btn == 'TMAndonButton':
        Var.andon = False
        Var.andonCount += Var.unresponded
        Var.unresponded = 0
        app.setButtonBg('TMAndonButton', GUIConfig.buttonColor)

    """ reject 1 part """
    if btn == 'Reject + 1':
        Var.rejects += 1
        yields = (Var.parts_delivered - Var.rejects) / Var.parts_delivered
        app.setButton('Reject + 1', 'Reject + 1\nRejects: %s\nYields: %.02f' % (Var.rejects, yields))
        app.setMeter('partsOutMeter', (Var.parts_delivered / Var.demand) * 100,
                     '%s / %s Parts' % (Var.parts_delivered - Var.rejects, Var.demand - Var.rejects))
        print('Bye, part! Have fun on your first day at bearings!')


def recalculate():
    """ resets labels for available time, takt, tct, seq time, and partsOutMeter """
    Var.available_time = sum(Var.sched.blockSeconds)
    # Var.demand = int(app.getEntry('demand'))
    Var.takt = Var.available_time / Var.demand
    Var.tct = get_tct()
    try:  # these labels only exist on the worker type
        # Var.partsper = int(app.getEntry('partsper'))
        Var.sequence_time = Var.tct * Var.partsper
        app.setLabel('Takt', countdown_format(int(Var.takt)))
        app.setLabel('TCT', countdown_format(Var.tct))
        app.setLabel('Seq', countdown_format(int(Var.sequence_time)))
        app.setMeter('partsOutMeter', (Var.parts_delivered / Var.demand) * 100,
                     '%s / %s Parts' % (Var.parts_delivered, Var.demand))
    except ItemLookupError:
        print('skipping certain labels belonging to Worker')
    try:  # these labels only exist on the Server/Team Lead Type
        app.setLabel('takt2', countdown_format(int(Var.takt)))
        app.setEntry('demand', Var.demand)
    except ItemLookupError:
        print('skipping certain labels belonging to Leader')


def key_press(key):
    """ handles physical key presses (keyboard or pedal) """
    if key == '1' or key == '<space>':
        cycle()
    if key == '<F11>':
        app.exitFullscreen() if app.getFullscreen() else app.setFullscreen()
    if key == '2':
        reset()


def menu_press(btn):
    """ handles all options under the File menu """
    if btn == 'Fullscreen':
        key_press('<F11>')
    elif btn == 'Exit':
        app.stop()
    elif btn == 'Run Tracker':
        os.system('ssh pi@192.168.42.1 < ./run-tracker.sh&')

def set_sequence_number(option_box):
    """ sets the sequence number as an identifier (should be unique in the cell) """
    Var.seq = int(app.getOptionBox(option_box))
    c = configparser.ConfigParser()
    c.read('install.ini')
    c['Var']['seq'] = str(Var.seq)
    with open('install.ini', 'w') as configfile:  # saves sequence number to install.ini to load every time
        c.write(configfile)


def shift_guesser():
    """ returns the current shift based on the time """
    Var.now = datetime.datetime.now()
    return 'Grave' if Var.now.hour >= 23 else 'Swing' if Var.now.hour >= 15 \
        else 'Day' if Var.now.hour >= 7 else 'Grave'


Var.shift = shift_guesser()  # set the current shift upon startup


def countdown_format(seconds: int):
    """ takes seconds and returns ":SS", "MM:SS", or "HH:MM:SS" """
    hours, minutes = divmod(seconds, 3600)
    minutes, seconds = divmod(minutes, 60)
    hour_label = '%s:%02d' % (hours, minutes)
    minute_label = '%s:%02d' % (minutes, seconds)
    second_label = ':%02d' % seconds
    return Var.tCycle if hours < 0 else hour_label if hours else minute_label if minutes else second_label


def shift_adjust(btn):
    """ option on TL computer to adjust the start and stop times of the shift"""
    Var.schedule_edited = True  # variable to show that this function has ran
    app.setOptionBox('Schedule: ', 'Custom', callFunction=False)  # no longer using a stock schedule
    session = create_session()
    old_schedule = session.query(Schedule).filter(Schedule.id == Var.sched.id).first()
    try:  # use one that exists, or create new one
        new_schedule = session.query(Schedule).filter(Schedule.shift == app.getOptionBox('Shift: '),
                                                      Schedule.name == 'Custom').one()
    except NoResultFound:
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
    app.setLabel('block%sTotal' % str(block), str(Var.sched.blockSeconds[block-1]) + '\nSecs')
    Var.available_time = sum(Var.sched.blockSeconds)
    Var.takt = int(Var.available_time / Var.demand)
    app.setLabel('totalTime', Var.available_time)
    app.setLabel('takt2', countdown_format(Var.takt))


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
    try:
        kpi = session.query(KPI).filter(KPI.d == datetime.date.today(),
                                        KPI.shift == shift).one()
    except NoResultFound:
        if app.yesNoBox('New Shift?', 'Create the plan for the current shift?'):
            kpi = KPI(d=datetime.date.today(), shift=shift, demand=312)
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
        for label in ['block%s' % block, 'block%sTotal' % block]:
            try:
                app.removeLabel(label)
            except ItemLookupError:
                print('block %s does not exist. Ignoring command to delete labels.' % block)
        for button in ['startUP%s' % block, 'startDN%s' % block,
                       'endUP%s' % block, 'endDN%s' % block]:
            try:
                app.removeButton(button)
            except ItemLookupError:
                pass
        try:
            app.removeLabelFrame('%s Block' % GUIVar.ordinalList[block])
        except ItemLookupError:
            pass
        print('removing block %s labels' % block)
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
                 'block%sTotal' % block:    ['%s\nSecs' % block_time, 0, 3, 2],
                 # 'block%sPercent' % block:  [('%.2f' % percent)[2:] + '% of available time', 2, 0]
                 }
            for label in d:
                app.addLabel(title=label, text=d[label][0], row=d[label][1], column=d[label][2], rowspan=d[label][3])
            if c['Install']['type'] != 'Worker':
                for button in buttons:
                    e = len(button)
                    app.addButton(title=button, func=buttons[button][0],
                                  row=buttons[button][1], column=buttons[button][2])
                    app.setButton(button, '+' if button[e-3:e-1] == 'UP' else '-')
    app.stopFrame()
    Var.mark = datetime.datetime.now()
    print('finished with app.function.read_time_file')
