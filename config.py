import datetime
import os
import configparser

basedir = "P:/Talladega Factory/Swing/Rylan Sturm/Company Takt Timer/Data"
c = configparser.ConfigParser()
c.read('install.ini')


class GUIConfig(object):
    db_file             = 'app.db'
    platform            = os.sys.platform
    title               = 'Takt Timer'
    windowSize          = {'linux': 'fullscreen',
                           'win32': None}
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
    demandIncrements    = ['1']
    partsperIncrements  = ['1']
    partsOutIncrements  = ['1']
    fileMenuList        = ['Fullscreen', '-', 'Exit']
    seqMenuList         = list(range(1, 10))
    keys                = ['1', '<space>', '<F11>']
    shifts              = ['Grave', 'Day']
    areas               = ['Talladega', 'Charlotte', 'Indy', 'Brickyard',
                           'Richmond', 'Bristol', 'Sonoma', 'Texas',
                           'Atlanta', 'Fontana', 'Monaco']
    scheduleTypes       = ['Regular', 'Department Lunch', 'Pit Stop', '', 'Custom']
    ordinalList         = ['', 'First', 'Second', 'Third', 'Fourth',
                           'Fifth', 'Sixth', 'Seventh', 'Eighth']
    target_window       = 3
    minimum_tct         = 45
