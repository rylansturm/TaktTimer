import os
import sys
import datetime
import configparser
sys.path.insert(0, '/home/pi/TaktTimer/venv/Lib/site-packages')

while True:
    if os.path.exists('install.ini'):
        c = configparser.ConfigParser()
        c.read('install.ini')
        print('importing app at %s' % datetime.datetime.now())
        from app import app
        if c['Install']['type'] == 'Worker':
            print('importing layout at %s' % datetime.datetime.now())
            from app import layout_worker
            print('importing GUIVar at %s' % datetime.datetime.now())
            from config import GUIVar
            print('importing app.functions.* at %s' % datetime.datetime.now())
            from app.functions import *
        else:
            from app import layout_server
            from config import *
            from app.functions import *

        for key in GUIVar.keys:
            app.bindKey(key, key_press)

        print('starting app at %s' % datetime.datetime.now())
        app.go()
        break
    else:
        try:
            from installation import *
            inst.go()
        except:
            print('installation failed')
            break
