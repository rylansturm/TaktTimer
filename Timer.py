# Run this file to launch the TaktTimer app

"""
This app was designed by Rylan Sturm at US Synthetic. It came from an apparent need
to see Takt Time abnormalities within a flow cell. Operators were previously unable
to relate to Takt Time in a manner that allowed for effective problem solving and
standard creation.

If anyone comes across this app on the currently public github repository, it is free
for use. Contact me at the address below, I would love to follow your usage and give
and get support on improving its functionality.

For assistance contact sturm.rw@gmail.com
"""

import os
import sys
import datetime
import configparser
sys.path.insert(0, '/home/pi/TaktTimer/venv/Lib/site-packages')  # All dependencies are available in the venv

while True:
    """ Check for initialization file, then run accordingly """
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
        """ If no initialization file exists, run the installer. """
        try:
            from installation import *
            inst.showSplash("TaktTimer\nInstall", "#20EF45")
            inst.go()
        except Exception:
            print('installation failed')
            break
