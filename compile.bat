@echo off
del .\dist\* /F /Q
pyinstaller --noconfirm --onefile --windowed --add-data "./assets;assets/" --icon "./assets/hue-sync.ico"  "./hue-sync.py"