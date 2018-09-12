from models import *
from appJar import gui
import datetime


class Var:
    length = 0


def shift_guesser():
    return 'Grave' if datetime.datetime.now().hour >= 23 else 'Swing' if datetime.datetime.now().hour >= 15 \
        else 'Day' if datetime.datetime.now().hour >= 7 else 'Grave'


session = create_session()
kpi = session.query(KPI).filter(KPI.shift == shift_guesser(),
                                KPI.d == datetime.date.today()).one()

app = gui()


def update():
    sequences = session.query(Cycles).filter(Cycles.kpi_id == kpi.id)\
                .distinct(Cycles.seq).order_by(Cycles.seq.asc()).group_by(Cycles.seq).order_by(Cycles.d.desc())
    if len(sequences.all()) != Var.length:
        Var.length = len(sequences.all())
        app.removeAllWidgets()
        for seq in sequences.all():
            with app.labelFrame('Sequence %s' % seq.seq):
                app.setSticky('ew')
                app.addMeter('sequence%sMeter' % seq.seq)
                app.setMeterFill('sequence%sMeter' % seq.seq, 'green')
    for seq in sequences.all():
        app.setMeter('sequence%sMeter' % seq.seq, (seq.delivered / kpi.demand) * 100,
                     '%s / %s' % (seq.delivered, kpi.demand))


app.registerEvent(update)
app.setPollTime(5000)

app.go()
