import os
import winshell
from win32com.client import Dispatch

desktop = getattr(winshell, 'desktop')()
path = os.path.join(desktop, "Auto Presensi.lnk")

target = r"c:\repos\absensi\Start_Auto_Presensi.bat"
wDir = r"c:\repos\absensi"
icon = r"shell32.dll, 43"

shell = Dispatch('WScript.Shell')
shortcut = shell.CreateShortCut(path)
shortcut.Targetpath = target
shortcut.WorkingDirectory = wDir
shortcut.IconLocation = icon
shortcut.WindowStyle = 7 # Minimized
shortcut.save()

print("Shortcut created successfully at:", path)
