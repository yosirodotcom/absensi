Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = oWS.ExpandEnvironmentStrings("%USERPROFILE%\Desktop\AutoPresensi.lnk")
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "c:\repos\absensi\Start_Auto_Presensi.bat"
oLink.WorkingDirectory = "c:\repos\absensi"
oLink.IconLocation = "shell32.dll,43"
oLink.WindowStyle = 7
oLink.Save
