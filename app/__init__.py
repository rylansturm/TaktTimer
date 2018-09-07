import sys, os
sys.path.insert(0, 'venv/Lib/site-packages')
from appJar import gui
from config import GUIConfig, GUIVar

try:
    app = gui(GUIConfig.title, GUIConfig.windowSize[GUIConfig.platform])
except KeyError:
    app = gui(GUIConfig.title, 'fullscreen')
app.setFont(size=GUIConfig.normalFont)
