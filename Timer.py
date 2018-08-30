from app import app
from app import layout
from config import GUIVar
from app.functions import *

for key in GUIVar.keys:
    app.bindKey(key, key_press)

app.go()
