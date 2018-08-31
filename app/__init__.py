from appJar import gui
from config import GUIConfig, GUIVar

try:
    app = gui(GUIConfig.title, GUIConfig.windowSize[GUIConfig.platform])
except KeyError:
    app = gui(GUIConfig.title, 'fullscreen')
app.setFont(size=GUIConfig.normalFont)