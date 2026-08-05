import sys
import win32com.client
print("Python executable:", sys.executable)
print("win32com present:", 'win32com' in sys.modules or True)
xl = win32com.client.gencache.EnsureDispatch("Excel.Application")
xl.Visible = True
print("Excel visible:", xl.Visible)
rng = xl.InputBox("Click a cell (or Cancel)", Type=8)
print("Selection:", rng.Address if rng else "Canceled")