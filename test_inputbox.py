import win32com.client
xl = win32com.client.Dispatch("Excel.Application")
xl.Visible = True
rng = xl.InputBox("Click a cell (or Cancel)", Type=8)
print("Selection:", rng.Address if rng else "Canceled")