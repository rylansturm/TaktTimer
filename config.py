import datetime
import os

basedir = "P:/Talladega Factory/Swing/Rylan Sturm/Company Takt Timer/Data"

class GUIConfig(object):
    platform            = os.sys.platform
    title               = 'Takt Timer'
    windowSize          = {'linux': 'fullscreen',
                           'win32': '800x480'}
    normalFont          = 16
    smallFont           = 'arial 12'
    mediumFont          = 'arial 24'
    largeFont           = 'arial 78'
    tCycleFont          = 'arial 170'
    appBgColor          = 'light grey'
    targetColor         = 'yellow'
    andonColor          = 'red'
    partsOutMeterFill   = 'blue'
    timeMeterFill       = 'purple'
    tabs                = ['Main', 'Data', 'Setup']
    max_parts_delivered = 500
    schedule_increment  = datetime.timedelta(minutes=5)


class GUIVar(object):
    demandIncrements    = ['24', '1']
    partsperIncrements  = ['24', '1']
    fileMenuList        = ['Fullscreen', '-', 'Exit']
    keys                = ['1', '<space>', '<F11>']
    shifts              = ['Grave', 'Day', 'Swing']
    areas               = ['Talladega', 'Charlotte', 'Indy', 'Brickyard',
                           'Richmond', 'Bristol', 'Sonoma', 'Texas',
                           'Atlanta', 'Fontana', 'Monaco']
    scheduleTypes       = ['Regular', 'Pit Stop', 'Department Lunch']
    ordinalList         = ['', 'First', 'Second', 'Third', 'Fourth',
                           'Fifth', 'Sixth', 'Seventh', 'Eighth']
    target_window       = 3
    minimum_tct         = 45
