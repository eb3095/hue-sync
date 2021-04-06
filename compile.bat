@echo off
pyinstaller --noconfirm --onefile --windowed --icon "./assets/hue-sync.ico"  "./hue-sync.py"