from models import *
from appJar import gui
import datetime


class Var:
    length = 0
    poll_count = 0


def shift_guesser():
    return 'Grave' if datetime.datetime.now().hour >= 23 else 'Swing' if datetime.datetime.now().hour >= 15 \
        else 'Day' if datetime.datetime.now().hour >= 7 else 'Grave'


session = create_session()
kpi = session.query(KPI).filter(KPI.shift == shift_guesser(),
                                KPI.d == datetime.date.today()).one()

app = gui()
app.setFont(size=24)

def update():
    session = create_session()
    cycles = session.query(Cycles).filter(Cycles.kpi_id == kpi.id)
    sequences = []
    for i in cycles.order_by(Cycles.seq.asc()).group_by(Cycles.seq).all():
        sequences.append(i.seq)
    if len(sequences) != Var.length:
        Var.length = len(sequences)
        app.removeAllWidgets()
        for seq in sequences:
            with app.labelFrame('Sequence %s' % seq):
                app.setSticky('ew')
                app.addMeter('seq%sMeter' % seq, row=0, column=0, colspan=4)
                app.setMeterFill('seq%sMeter' % seq, 'green')
                app.addLabel('seq%sAVGLabel' % seq, 'Batting AVG: ', 1, 0)
                app.addLabel('seq%sAVG' % seq, 'avg', 1, 1)
    for seq in sequences:
        cycle = cycles.filter(Cycles.seq == seq).order_by(Cycles.d.desc())
        avg = '%.3f' % (len(cycle.filter(Cycles.hit == 1).all()) / len(cycle.all()))
        app.setMeter('seq%sMeter' % seq, (cycle.first().delivered / kpi.demand) * 100,
                     '%s / %s' % (cycle.first().delivered, kpi.demand))
        app.setLabel('seq%sAVG' % seq, avg)
    session.close()



app.registerEvent(update)
app.setPollTime(5000)

app.go()
