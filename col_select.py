import PySimpleGUI as sg

cols = {}
temp = ['SRPID', 'Consultant', 'Sample_Date', 'Location_Name', 'Sample_Time', 'Duplicate',
           'Matrix', 'Address', 'Well_Name', 'Sample_Type', 'Date_to_Lab', 'Sample_Method',
           'Lab_ID', 'Analysis_Date', 'Lab_Name', 'Analyte', 'CASN', 'Filt_Unfilt', 'Result',
           'Result_Unit', 'Flag', 'Method_Detection_Limit', 'Analysis_Method']
ref_cols = []
current_vals = {}
version = ''

def item_row(item_num, default=''):
    row = [sg.pin(sg.Col([[sg.Button(sg.SYMBOL_X, border_width=0, button_color=(sg.theme_text_color(), sg.theme_background_color()), k=('-DEL-', item_num), tooltip='Delete this item'),
                            sg.Combo(list(cols.values()), size=(30, 7), k=('-OPT-', item_num), enable_events=True, default_value=default)]], k=('-ROW-', item_num)))]
    return row

def makewin():
    layout = [
        [sg.Text('Format')],
        [sg.Frame(
            'Columns',
            [[sg.Column(
                [item_row(0)],
                key='-TRACK-',
                size=(460, 360),
                scrollable=True,
                vertical_scroll_only=True,
                expand_x=True,
                pad=(0, 6),
            )]],
            expand_x=True,
        )],
        [sg.pin(sg.Text(size=(35, 1), key='-REFRESH-'))],
        [sg.Button('Add Row', key='-ADD-'),
            sg.Button('Continue', key='-CONT-', disabled=True),
            sg.Radio('Unified', group_id='group1', key='-U-', enable_events=True),
            sg.Radio('Separate', group_id='group1', key='-S-', enable_events=True)]
    ]
    window = sg.Window(
        'Choose Columns',
        layout,
        metadata=0,
        enable_close_attempted_event=True,
        finalize=True,
        resizable=True,
        size=(540, 520),
    )
    return window

def col_choose(user_col):
    template = sg.popup_yes_no('Populate MASTER_TEMPLATE?', title='Template')
    default = set()
    default.update(temp)
    default.update(user_col)
    ref_cols = list(sorted(default))
    for x in range(0, len(ref_cols)):
        cols[x] = ref_cols[x]
    window = makewin()
    if template == 'Yes':
        window['-OPT-', 0].update(values=list(cols.values()), set_to_index=ref_cols.index('SRPID'), size=(30,7))
        del cols[ref_cols.index('SRPID')]
        for col in temp[1:]:
            window.metadata += 1
            window.extend_layout(window['-TRACK-'], [item_row(window.metadata, col)])
            current_vals[window.metadata] = [ref_cols.index(col), col]
            del cols[ref_cols.index(col)]
        window.read(timeout=0)
        window['-TRACK-'].contents_changed()
        window.refresh()
    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT:
            sg.popup_auto_close('Please Finish Selection')
            continue
        if event in (sg.WIN_CLOSED, None):
            window.close()
            return [], version
        if event in ['-U-', '-S-']:
            window['-CONT-'].update(disabled=False)
        if event == '-CONT-':
            if values.get('-U-'):
                version = 'Unified'
            else:
                version = 'Separate'
            break
        if event == '-ADD-':
            window.metadata += 1
            window.extend_layout(window['-TRACK-'], [item_row(window.metadata)])
            window['-TRACK-'].contents_changed()
        elif event[0] == '-DEL-':
            window[('-ROW-', event[1])].update(visible=False)
            if event[1] in current_vals:
                cols[ref_cols.index(current_vals[event[1]][1])] = current_vals[event[1]][1]
            for row in list(current_vals):
                    sel = list(sorted(cols.values()))
                    sel.insert(0, current_vals[row][1])
                    window[('-OPT-', row)].update(values=list(sel), set_to_index=0, size=(30, 7))
            window['-TRACK-'].contents_changed()
        if event[0] == '-OPT-':
            if event[1] in current_vals:
                x = current_vals[event[1]][0]
                cols[x] = ref_cols[x]
            del cols[ref_cols.index(values[('-OPT-', event[1])])]
            current_vals[event[1]] = [ref_cols.index(values[('-OPT-', event[1])]), values[('-OPT-', event[1])]]
            for row in list(current_vals):
                if row != event[1]:
                    sel = list(sorted(cols.values()))
                    sel.insert(0, current_vals[row][1])
                    window[('-OPT-', row)].update(values=list(sel), set_to_index=0, size=(30, 7))            

    chosen = []
    for x in range(0, window.metadata + 1):
        if window[('-ROW-', x)].visible:
            chosen.append(values[('-OPT-', x)])

    window.close()
    return chosen, version