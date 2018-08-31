from app import app
from config import GUIConfig, GUIVar
from app.functions import *


app.registerEvent(counting)

# Drop down menus at top left #
app.addMenuList('File', GUIVar.fileMenuList, menu_press)


# Tabbed Frame that holds the whole GUI #
with app.tabbedFrame('Tabs'):

    # Main tab # main screen, for seeing TT, TCT, tCycle, partsAhead, etc #
    with app.tab(GUIConfig.tabs[0]):
        with app.labelFrame('Remaining Cycle Time', row=0, column=0, rowspan=5):
            app.setSticky('new')
            app.setLabelFrameAnchor('Remaining Cycle Time', 'n')
            # Main Cycle Time
            app.addLabel('tCycle', 0, row=0, column=0, colspan=4)
            app.getLabelWidget('tCycle').config(font=GUIConfig.tCycleFont)
            # Meter for parts produced
            app.addMeter('partsOutMeter', row=2, column=0, colspan=4)
            app.setMeter('partsOutMeter', 0, '0 / 0 Parts')
            app.setMeterFill('partsOutMeter', GUIConfig.partsOutMeterFill)
            # Clock display and label showing time for next break
            app.addLabel('timeLabel', 'Time:', row=3, column=0)
            app.addLabel('time', 'now o\'clock', row=3, column=1)
            app.addLabel('nextBreakLabel', 'Next Break:', row=3, column=2)
            app.addLabel('nextBreak', 'later o\'clock', row=3, column=3)
            # Meter for time elapsed / total available time
            app.addMeter('timeMeter', row=4, column=0, colspan=4)
            app.setMeter('timeMeter', 0, '0 / 0 Seconds Passed')
            app.setMeterFill('timeMeter', GUIConfig.timeMeterFill)

        with app.labelFrame('data', row=0, column=1, rowspan=5, hideTitle=True):
            app.setSticky('new')
            with app.labelFrame('times', row=0, colspan=2, hideTitle=True):
                app.setSticky('new')
                timesList = ['Takt', 'TCT', 'Seq']
                for i in range(len(timesList)):
                    app.addLabel('%sLabel' % timesList[i], timesList[i], row=0, column=i)
                    app.addLabel(timesList[i], 0, row=1, column=i)
            with app.labelFrame('cycles', row=1, column=0, colspan=2, rowspan=2, hideTitle=True):
                app.setSticky('new')
                app.addLabel('lastCycleLabel', 'Last Cycle', row=0, column=0)
                app.addLabel('lastCycle', 0, row=1, column=0)
                app.addLabel('avgCycleLabel', 'Average\n  Cycle', row=0, column=1)
                app.addLabel('avgCycle', 0, row=1, column=1)
            with app.labelFrame('Missed', row=3, column=0, colspan=2, rowspan=2):
                app.setSticky('new')
                app.setLabelFrameAnchor('Missed', 'n')
                app.addLabel('earlyLabel', 'Early', row=0, column=0)
                app.addLabel('early', 0, row=1, column=0)
                app.addLabel('lateLabel', 'Late', row=0, column=1)
                app.addLabel('late', 0, row=1, column=1)
                app.addButton('leadUnverifiedButton', press, row=0, column=2)
                app.setButton('leadUnverifiedButton', 'TL\nUnverified')
                app.addLabel('leadUnverified', 0, row=1, column=2)
            app.addLabel('partsAheadLabel', ' Parts\nAhead', row=5, column=0)
            app.addLabel('partsAhead', 0, row=6, column=0)
            app.addButton('Reject + 1', press, row=5, column=1, rowspan=2)

    # DATA tab #
    with app.tab(GUIConfig.tabs[1]):
        app.addMessage('cycleTimes', [])
        app.setMessageAspect('cycleTimes', 500)
        app.addButton('Machine Down\nAlarm Override', press)
        app.addLabel('battingAVG', 'N/A')

    # Setup tab #
    with app.tab(GUIConfig.tabs[2]):
        with app.labelFrame('Presets', row=0, column=0):
            app.setSticky('new')
            app.addOptionBox('Area: ', ['Select'] + GUIVar.areas)
            app.setOptionBoxChangeFunction('Area: ', enable_sched_select)
            app.addOptionBox('Shift: ', GUIVar.shifts)
            app.setOptionBox('Shift: ', 'Day')
            app.addOptionBox('Schedule: ', GUIVar.scheduleTypes)
            for box in ['Shift: ', 'Schedule: ']:
                app.disableOptionBox(box)
                app.setOptionBoxChangeFunction(box, read_time_file)
        with app.frame('buttons', row=1, column=0):
            app.addButton('Go', press, row=3, column=0, colspan=2)
            app.disableButton('Go')
            app.addButton('Recalculate', recalculate, row=4, column=0, colspan=2)
            app.addLabel('taktLabel2', 'Takt', row=3, column=2)
            app.addLabel('takt2', 0, row=4, column=2)
        with app.labelFrame('Variables', row=0, column=1, rowspan=2):
            app.setSticky('w')
            app.addLabelEntry('demand', row=0, column=0, colspan=2)
            app.setEntry('demand', 0)
            app.setLabel('demand', 'Demand: ')
            app.addCheckBox('Parts Out', row=3, column=0)
            app.setCheckBoxChangeFunction('Parts Out', enable_parts_out)
            app.addSpinBox('Parts Delivered', list(range(GUIConfig.max_parts_delivered, -1, -1)), row=3, column=1)
            app.setSpinBox('Parts Delivered', 0)
            app.addButton('Set', press, row=3, column=2)
            # app.disableLabel('Parts Delivered')
            app.disableSpinBox('Parts Delivered')
            app.disableButton('Set')
            with app.labelFrame('demandIncrementFrame', row=0, column=2, rowspan=2, hideTitle=True):
                app.setSticky('ew')
                inc = GUIVar.demandIncrements
                for i in range(len(inc)):
                    app.addButton('%02dUPDemand' % int(inc[i]), demand_set, row=0, column=i + 1)
                    app.addButton('%02dDNDemand' % int(inc[i]), demand_set, row=1, column=i + 1)
                    app.setButton('%02dUPDemand' % int(inc[i]), '+%s' % inc[i])
                    app.setButton('%02dDNDemand' % int(inc[i]), '-%s' % inc[i])
            app.addLabelEntry('partsper', row=2, column=0, colspan=2)
            app.setEntry('partsper', 2)
            app.setLabel('partsper', 'Parts \nper cycle: ')
            with app.labelFrame('partsperIncrementFrame', row=2, column=2, hideTitle=True):
                app.setSticky('new')
                inc = GUIVar.partsperIncrements
                for i in range(len(inc)):
                    app.addButton('%02dUPPartsper' % int(inc[i]), partsper_set, row=0, column=i + 1)
                    app.addButton('%02dDNPartsper' % int(inc[i]), partsper_set, row=1, column=i + 1)
                    app.setButton('%02dUPPartsper' % int(inc[i]), '+%s' % inc[i])
                    app.setButton('%02dDNPartsper' % int(inc[i]), '-%s' % inc[i])
        with app.labelFrame('Parameters', row=2, column=0, colspan=2):
            app.setSticky('new')
            with app.frame('Shift', colspan=4):
                app.addLabel('start-end', 'time-time', 0, 0)
                app.addLabel('start-endTotal', 'Total Seconds', 0, 1)
                # app.addLabel('start-endPercent', 'Percent', 1, 0)
            for block in range(1, 5):
                with app.labelFrame('%s Block' % GUIVar.ordinalList[block], row=1, column=block-1):
                    app.setSticky('new')
                    app.setLabelFrameAnchor('%s Block' % GUIVar.ordinalList[block], 'n')
                    app.addLabel('block%s' % block, 'time-time', 0, 0)
                    app.addLabel('block%sTotal' % block, 'Seconds', 1, 0)
                    # app.addLabel('block%sPercent' % block, 'Percent', 2, 0)


for i in GUIConfig.tabs:
    app.setTabBg('Tabs', i, GUIConfig.appBgColor)

app.setTabbedFrameSelectedTab('Tabs', 'Setup')
for tab in ['Main', 'Data']:
    app.setTabbedFrameDisabledTab('Tabs', tab)
