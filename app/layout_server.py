from app.functions import *


app.registerEvent(counting_server)


# Drop down menus at top left #
app.addMenuList('File', GUIVar.fileMenuList, menu_press)
app.addMenuList('Options', ['Update'], menu_press)

print('creating tabs for server')
# Tabbed Frame that holds the whole GUI #
with app.tabbedFrame('Tabs'):
    app.setBg(GUIConfig.appBgColor)

    # Setup tab #
    with app.tab('Setup'):
        app.setBg(GUIConfig.appBgColor)
        with app.frame('Presets', row=0, column=0):
            app.setSticky('new')
            app.setBg(GUIConfig.appBgColor)
            app.addLabel('timestamp',
                         datetime.datetime.now().strftime("%a, %b %d, '%y\n    %I:%M:%S %p"))
            # app.addOptionBox('Area: ', ['Select'] + GUIVar.areas)
            # app.setOptionBoxChangeFunction('Area: ', enable_sched_select)
            app.addLabelOptionBox('Shift: ', GUIVar.shifts)
            app.addLabelOptionBox('Schedule: ', GUIVar.scheduleTypes)
            app.setOptionBoxChangeFunction('Shift: ', change_schedule_box_options)
            app.setOptionBoxChangeFunction('Schedule: ', determine_time_file)
            app.setOptionBox('Shift: ', shift_guesser())
        with app.frame('info', row=2, column=0):
            app.setBg(GUIConfig.appBgColor)
            # app.addButton('Set', set_kpi, row=3, column=0, colspan=2)
            # app.addButton('Recalculate', recalculate, row=4, column=0, colspan=2)
            app.addLabel('totalTimeLabel', 'Total Available Time', row=3, column=0)
            app.addLabel('totalTime', Var.available_time, row=4, column=0)
            app.addLabel('taktLabel2', 'Takt', row=3, column=1)
            app.addLabel('takt2', 0, row=4, column=1)
        with app.labelFrame('Demand', row=1, column=0):
            app.setBg(GUIConfig.appBgColor)
            app.setSticky('w')
            app.addLabelNumericEntry('demand', row=0, column=0, colspan=2)
            app.setEntry('demand', 0)
            app.setLabel('demand', 'Demand: ')
            with app.labelFrame('demandIncrementFrame', row=0, column=2, rowspan=2, hideTitle=True):
                app.setSticky('ew')
                app.setBg(GUIConfig.appBgColor)
                inc = GUIVar.demandIncrements
                for i in range(len(inc)):
                    app.addButton('%02dUPDemand' % int(inc[i]), demand_set, row=0, column=i + 1)
                    app.addButton('%02dDNDemand' % int(inc[i]), demand_set, row=1, column=i + 1)
                    app.setButton('%02dUPDemand' % int(inc[i]), '+%s' % inc[i])
                    app.setButton('%02dDNDemand' % int(inc[i]), '-%s' % inc[i])
        with app.labelFrame('Plan Cycle Time', row=0, column=1, rowspan=3, hideTitle=True):
            app.setSticky('n')
            app.addLabel('plan_cycle_label', 'Plan Cycle Time')
            app.addButtons(['tct_up1', 'tct_up5'], set_tct)
            app.setButton('tct_up1', "+1")
            app.setButton('tct_up5', "+5")
            app.addLabel('plan_cycle', 60)
            app.addButtons(['tct_dn1', 'tct_dn5'], set_tct)
            app.setButton('tct_dn1', "-1")
            app.setButton('tct_dn5', "-5")
            app.addButton('log_tct', log_tct)
            app.setButton('log_tct', 'Set PCT on all timers')
            app.addButton('remove_tct', log_tct)
            app.setButton('remove_tct', 'Remove PCT from all timers')
    with app.tab('Schedule'):
        app.setBg(GUIConfig.appBgColor)
        with app.frame('Parameters', row=0, column=1, rowspan=3):
            app.setSticky('new')
            app.setBg(GUIConfig.appBgColor)
            # with app.frame('Shift', colspan=4):
            #     app.addLabel('start-end', 'time-time', 0, 0)
            #     app.addLabel('start-endTotal', 'Total Seconds', 0, 1)
            #     # app.addLabel('start-endPercent', 'Percent', 1, 0)
            for block in range(1, 5):
                with app.labelFrame('%s Block' % GUIVar.ordinalList[block], row=1, column=block-1):
                    app.setSticky('new')
                    app.setLabelFrameAnchor('%s Block' % GUIVar.ordinalList[block], 'n')
                    app.addLabel('block%s' % block, 'time-time', 0, 0)
                    app.addLabel('block%sTotal' % block, 'Seconds', 1, 0)
                    # app.addLabel('block%sPercent' % block, 'Percent', 2, 0)
        with app.frame('Meta', row=0, column=2):
            app.setSticky('new')
            app.setBg(GUIConfig.appBgColor)
            app.addOptionBox('Area', ['Ace Post Leach', 'Brickyard', 'Talladega'])
            app.setOptionBoxChangeFunction('Area', set_area)
            app.setOptionBox('Area', c['Var']['Area'])
print('done with creating layout at %s seconds' % (datetime.datetime.now()-Var.time_open).total_seconds())
read_time_file(shift=Var.shift, name=Var.sched.name)

with app.subWindow('New Schedule', modal=True, transient=True):
    app.addLabel('saveDialog', 'Save New Schedule', row=0, column=0, colspan=5)
    app.addEntry('newScheduleName', row=1, column=2, colspan=3)
    app.addMessage('Fake', 'Fake Message Here', row=2, column=2, colspan=3)

app.setBg(GUIConfig.appBgColor)
