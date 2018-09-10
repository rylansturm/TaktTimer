from appJar import gui
from config import GUIConfig
import configparser
import datetime
from models import *
from db_setup import *

file = 'install.ini'
c = configparser.ConfigParser()
c.read(file)


class Var:
    install_type = None


def set_type():
    Var.install_type = inst.getOptionBox('type')


def install():
    c['Install'] = {'date': str(datetime.date.today()),
                    'type': Var.install_type,
                    }
    c['Database'] = {'file': inst.getEntry('file')}
    if Var.install_type == 'Server':
        create_db(inst.getEntry('file'))
        for shift in [Grave, Day, Swing]:
            for sched in shift:
                session = create_session(inst.getEntry('file'))
                s = Schedule(name=sched, shift=('Grave' if shift == Grave\
                                                else 'Swing' if shift == Swing\
                                                else 'Day'))
                s.get_times(*list(shift[sched].values()))
                session.add(s)
                session.commit()
    with open(file, 'w') as configfile:
        c.write(configfile)
    inst.stop()


def file_picker():
    inst.setEntry('file', inst.saveBox('save', fileExt='.db'))


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
        inst.addEntry('file', row=1, column=0)
        inst.addButton('select', file_picker)
        inst.addButton('Install', install)
