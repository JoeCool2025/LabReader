import PySimpleGUI as sg

rkeys = {'-GW-': 'Groundwater', '-SOIL-': 'Soil', '-PORE-': 'Porewater', '-MIX-': 'Mixed'}

def make_selection_layout():
    return [
        [
            sg.Radio('Groundwater', group_id='group1', key='-GW-', enable_events=True),
            sg.Radio('Soil', group_id='group1', key='-SOIL-', enable_events=True),
            sg.Radio('Porewater', group_id='group1', key='-PORE-', enable_events=True),
            sg.Radio('Mixed', group_id='group1', key='-MIX-', enable_events=True),
        ],
        [sg.Button('Select', key='-SELECT-', disabled=True)],
    ]


def matrixselection():
    selection = sg.Window('Lab Selection', make_selection_layout(), modal=True)
    labtype = None

    while True:
        event, values = selection.read()
        if event in (sg.WIN_CLOSED, 'Cancel'):
            labtype = None
            try:
                selection.close()
            except:
                continue
            break

        if event in rkeys:
            selection['-SELECT-'].update(disabled=False)

        if event == '-SELECT-':
            selected_keys = [key for key in rkeys if values.get(key)]
            if selected_keys:
                labtype = rkeys[selected_keys[0]]
                selection.close()
                break

    return labtype