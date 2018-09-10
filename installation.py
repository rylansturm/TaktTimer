from appJar import gui
from config import GUIConfig
import configparser
import datetime
from models import create_db

file = 'install.ini'
c = configparser.ConfigParser()
c.read(file)


class Var:
    install_type = None


def set_type(install_type):
    Var.install_type = install_type


def install():
    c['Install'] = {'date': str(datetime.date.today()),
                    'type': Var.install_type,
                    }
    c['Database'] = {'file': inst.getEntry('database')}
    create_db(inst.getEntry('database'))
    with open(file, 'w') as configfile:
        c.write(configfile)
    inst.stop()


inst = gui('TaktTimer Installer', GUIConfig.windowSize[GUIConfig.platform])

with inst.pagedWindow('Pages'):
    with inst.page(sticky='news'):
        inst.addMessage('Installer0', 'Welcome to the Installer!')
    with inst.page(sticky='n'):
        inst.addMessage('Installer1', 'First, what type of install will this be?')
        inst.addOptionBox('type', ['-Select-', 'Server', 'Worker'])
        inst.setOptionBoxChangeFunction('type', set_type)
    with inst.page(sticky='n'):
        inst.addMessage('Installer2', 'Second, where will the data be stored?')
        inst.addFileEntry('database')
        inst.addButton('Install', install)
