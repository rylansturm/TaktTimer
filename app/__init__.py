from appJar import gui
from config import GUIConfig, GUIVar

app = gui(GUIConfig.title, GUIConfig.windowSize)
app.setOnTop(stay=True)
app.setFont(size=GUIConfig.normalFont)