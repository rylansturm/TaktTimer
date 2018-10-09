import datetime
import os
import configparser

c = configparser.ConfigParser()
c.read('install.ini')


class GUIConfig(object):
    """ Variables relative to layout and formatting of the GUI"""
    platform = os.sys.platform                          # for certain platform-specific functions
    title = 'Takt Timer'                                # Title of the app, displays on task bar and window header
    windowSize = {'linux': 'fullscreen',
                  'win32': None}                        # window size on relative platform
    fontSize = 16                                       # default font size for app
    tCycleFont = 'arial 170'                            # font size of the main counter
    appBgColor = 'light grey'                           # overall background color
    targetColor = 'yellow'                              # color used when timers are in the target cycle window
    andonColor = 'red'                                  # color used for abnormalities (late to cycle, parts behind)
    buttonColor = 'light grey'
    partsOutMeterFill = 'blue'                          # color of the meter displaying parts delivered
    timeMeterFill = 'purple'                            # color of the meter displaying time elapsed in the shift
    schedule_increment = datetime.timedelta(minutes=5)  # standard increment when TL shifts schedule via +/- buttons


class GUIVar(object):
    """ Other GUI-related variables, button values, list options, etc. """
    demandIncrements = ['24', '1']                              # +/- buttons for TL setting demand
    partsperIncrements = ['24', '1']                            # +/- buttons for OP setting partsper
    partsOutIncrements = ['24', '1']                            # +/- buttons for OP setting parts delivered
    fileMenuList = ['Fullscreen', '-', 'Exit']                  # The options under the 'file' menu
    seqMenuList = list(range(1, 10))                            # Sequences available to choose from
    keys = ['1', '<space>', '<F11>', '2']                       # The keys that need to be bound to keyPress func
    shifts = ['Grave', 'Day', 'Swing']                          # The available shifts
    areas = ['Talladega', 'Charlotte', 'Indy', 'Brickyard',     # US Synthetic areas, currently not in use in app
             'Richmond', 'Bristol', 'Sonoma', 'Texas',
             'Atlanta', 'Fontana', 'Monaco']
    scheduleTypes = ['Regular', 'Department Lunch',             # default list of schedule types
                     'Pit Stop', '', 'Custom']
    ordinalList = ['', 'First', 'Second', 'Third', 'Fourth',    # ordinals for some labels (ex: ordinalList[block])
                   'Fifth', 'Sixth', 'Seventh', 'Eighth']
    target_window = 3                                           # seconds of variation acceptable per part for 'hit'
    minimum_tct = 45                                            # TCT will never dip below this value
