from app.functions import *

app.registerEvent(counting_worker)
app.setPollTime(50)

# Drop down menus at top left #
app.addMenuList('File', GUIVar.fileMenuList, menu_press)
app.addMenuList('Help', ['Update'], menu_press)

print('creating tabs')
# Tabbed Frame that holds the whole GUI #
with app.tabbedFrame('Tabs'):

    """ Main tab - main screen, for seeing TT, TCT, tCycle, partsAhead, etc """
    with app.tab('Main'):
        with app.labelFrame('Remaining Cycle Time', row=0, column=0, rowspan=5):
            app.setSticky('new')
            app.setLabelFrameAnchor('Remaining Cycle Time', 'n')
            # Main Cycle Time
            app.addLabel('tCycle', 0, row=0, column=0, colspan=4)
            app.setLabelSubmitFunction('tCycle', andon)
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
                app.setLabelSubmitFunction('TCTLabel', use_tct)
                app.setLabelSubmitFunction('TCT', use_tct)
                app.setLabel('TCTLabel', 'PCT')
            with app.labelFrame('cycles', row=1, column=0, colspan=2, rowspan=2, hideTitle=True):
                app.setSticky('new')
                app.addLabel('lastCycleLabel', 'Last Cycle', row=0, column=0)
                app.addLabel('lastCycle', 0, row=1, column=0)
                app.addLabel('avgCycleLabel', 'Avg Cycle', row=0, column=1)
                app.addLabel('avgCycle', 0, row=1, column=1)
            with app.labelFrame('Missed', row=3, column=0, colspan=2, rowspan=2, hideTitle=True):
                app.setSticky('new')
                app.setLabelFrameAnchor('Missed', 'n')
                app.addLabel('earlyLabel', 'Early', row=0, column=0)
                app.addLabel('early', 0, row=1, column=0)
                app.addLabel('lateLabel', 'Late', row=0, column=1)
                app.addLabel('late', 0, row=1, column=1)
                app.addLabel('onTimeLabel', 'Target', row=3, column=0)
                app.addLabel('onTime', 0, row=4, column=0)
                app.addButton('TMAndonButton', press, row=3, column=1)
                app.setButton('TMAndonButton', 'Andons')
                app.setButtonBg('TMAndonButton', GUIConfig.buttonColor)
                app.addLabel('TMAndon', Var.andonCountMsg, row=4, column=1)
            app.addLabel('partsAheadLabel', '  Takt\n Parts\nAhead', row=5, column=0)
            app.addLabel('partsAhead', 0, row=6, column=0)
            app.addLabel('tctAheadLabel', '  PCT\n Parts\nAhead', row=5, column=1)
            app.addLabel('tctAhead', 0, row=6, column=1)
            # app.addButton('Reject + 1', press, row=5, column=1, rowspan=2)
            # app.setButtonBg('Reject + 1', GUIConfig.buttonColor)

    print('%s seconds to data tab' % (datetime.datetime.now()-Var.time_open).total_seconds())

    """ Data tab - go to this tab to adjust partsper, parts_delivered, and sequence """
    with app.tab('Data'):
        with app.frame('Presets', row=0, column=0, colspan=2):
            app.setSticky('new')
            app.setBg(GUIConfig.appBgColor)
            app.addLabel('timestamp',
                         datetime.datetime.now().strftime("%a, %b %d, '%y\n    %I:%M:%S %p"),
                         row=0, column=0, rowspan=2)
            # app.addOptionBox('Area: ', ['Select'] + GUIVar.areas)
            # app.setOptionBoxChangeFunction('Area: ', enable_sched_select)
            app.addLabel('Shift: ', Var.shift, row=0, column=1)
            app.addLabel('Schedule: ', Var.sched.name + ' Schedule', row=1, column=1)
            app.addLabel('block', Var.block, row=2, column=0)
            app.addLabel('battingAVG', 0, row=3, column=0)
            app.addLabel('Sequence #: Label', 'Sequence #', row=2, column=1)
            app.addOptionBox('Sequence #: ', GUIVar.seqMenuList, row=3, column=1)
            app.setOptionBox('Sequence #: ', int(Var.seq)-1)
            app.setOptionBoxChangeFunction('Sequence #: ', set_sequence_number)
            # app.setOptionBoxChangeFunction('Shift: ', change_schedule_box_options)
            # app.setOptionBoxChangeFunction('Schedule: ', determine_time_file)
            # app.setOptionBox('Shift: ', shift_guesser())
        with app.frame('buttons', row=2, column=0, colspan=2):
            app.addScrolledTextArea('cycleTimes')
        with app.labelFrame('Parts per Cycle', row=1, column=0, colspan=1):
            app.setBg(GUIConfig.appBgColor)
            app.setSticky('ew')
            app.addLabel('partsper', Var.partsper, row=0, column=0, colspan=2)
            # app.setEntry('partsper', Var.partsper)
            # app.setLabel('partsper', 'Parts per\nCycle: ')
            with app.labelFrame('partsperIncrementFrame', row=0, column=2, rowspan=2, hideTitle=True):
                app.setSticky('ew')
                app.setBg(GUIConfig.appBgColor)
                inc = GUIVar.partsperIncrements
                for i in range(len(inc)):
                    app.addButton('%02dUPPartsper' % int(inc[i]), partsper_set, row=0, column=i + 1)
                    app.addButton('%02dDNPartsper' % int(inc[i]), partsper_set, row=1, column=i + 1)
                    app.setButton('%02dUPPartsper' % int(inc[i]), '+%s' % inc[i])
                    app.setButton('%02dDNPartsper' % int(inc[i]), '-%s' % inc[i])
        with app.labelFrame('Parts Out', row=1, column=1):
            app.setBg(GUIConfig.appBgColor)
            app.setSticky('ew')
            app.addLabel('partsOut', row=0, column=0, colspan=2)
            # app.setEntry('partsOut', Var.parts_delivered)
            app.setLabel('partsOut', 'Parts\n Out:')
            with app.labelFrame('partsOutIncrementFrame', row=0, column=2, rowspan=2, hideTitle=True):
                app.setSticky('ew')
                app.setBg(GUIConfig.appBgColor)
                inc = GUIVar.partsOutIncrements
                for i in range(len(inc)):
                    app.addButton('%02dUPPartsOut' % int(inc[i]), parts_out_set, row=0, column=i + 1)
                    app.addButton('%02dDNPartsOut' % int(inc[i]), parts_out_set, row=1, column=i + 1)
                    app.setButton('%02dUPPartsOut' % int(inc[i]), '+%s' % inc[i])
                    app.setButton('%02dDNPartsOut' % int(inc[i]), '-%s' % inc[i])
        with app.frame('Parameters', row=0, column=2, rowspan=4):
            app.setSticky('news')
            app.setBg(GUIConfig.appBgColor)
            # with app.frame('Shift', colspan=4):
            #     app.addLabel('start-end', 'time-time', 0, 0)
            #     app.addLabel('start-endTotal', 'Total Seconds', 0, 1)
            #     # app.addLabel('start-endPercent', 'Percent', 1, 0)
            for block in range(1, 5):
                with app.labelFrame('%s Block' % GUIVar.ordinalList[block], row=1, column=block - 1):
                    app.setSticky('new')
                    app.setLabelFrameAnchor('%s Block' % GUIVar.ordinalList[block], 'n')
                    app.addLabel('block%s' % block, 'time-time', 0, 0)
                    app.addLabel('block%sTotal' % block, 'Seconds', 1, 0)
                    # app.addLabel('block%sPercent' % block, 'Percent', 2, 0)


read_time_file(shift=Var.shift, name=Var.sched.name)
print('done with creating layout at %s seconds' % (datetime.datetime.now()-Var.time_open).total_seconds())

for i in ['Main', 'Data']:
    app.setTabBg('Tabs', i, GUIConfig.appBgColor)
