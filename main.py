import PySimpleGUI as sg
from txt_reader import tsv_reader

current_sites = []

layout = [
    [sg.Button(button_text='Import Lab Data')],
    [sg.Text('Select currently available site'), sg.Combo(current_sites), sg.Text('Or create a new site'), sg.Input(default_text='')],
    [sg.HorizontalSeparator(thickness=4)],
    [sg.Button(button_text='Exit')]
]

window = sg.Window('Window Title', layout)
while True:
    event, values = window.read()

    if event == 'Exit' or event == sg.WIN_CLOSED:
        break
    if event == 'Import Lab Data':
        lab_file = sg.popup_get_file(message="Select Lab File", file_types=((".txt", "*.txt"), (".csv", "*.csv"), ("ALL Files", "*.*")))
        if lab_file.lower().endswith(".txt"):
            db_path = sg.popup_get_file(message='Select Existing Database\n(or cancel to create a new database)', file_types=(('.db', '*.db'),))
            tsv_reader(lab_file, db_path)
            print("TSV read")
        else:
            print(lab_file)
    