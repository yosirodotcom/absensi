@echo off
cd /d "c:\repos\absensi"

:: Start the python backend completely silently in the background
start /B "c:\users\kerja\appdata\local\python\pythoncore-3.14-64\python.exe" auto_click.py
exit
