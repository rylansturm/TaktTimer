import os


while True:
    if os.path.exists('install.ini'):

        from app import app
        from app import layout
        from config import GUIVar
        from app.functions import *

        for key in GUIVar.keys:
            app.bindKey(key, key_press)

        app.go()
        break

    else:
        try:
            from installation import *
            inst.go()
        except:
            print('installation failed')
            break
