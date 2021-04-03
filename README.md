# hue-sync
Single Hue LED Strip color syncing for PC.

# Description
This can be used to sync one "Hue Lamp" to a PC screen for color syncing. Theres a few
limitations which are strictly based on my personal use case.

This does NOT use the bridge! This is a DIRECT bluetooth connection!

* Only the primary screen is captured
* Only 1 device can be used
* Only every 10 pixels are computed due to performance
* The first "Hue Lamp" found via discovery will be used (I only have 1)

# Requirements
The required packages are listed in requirements.txt. Some packages don't work, or don't
work easily with python versions higher then 3.6. This was tested for Windows (Sorry).
It should work on linux though, might need tweaked!

You need to reset the strip with the phone app for this to work! Afterwards pair it once
with your PC to get it to work again.

You will obviously need bluetooth on your PC.

# Install
```
git clone https://github.com/eb3095/hue-sync.git
cd hue-sync
python -m pip install -r .\requirements.txt
```

# Usage
```
python .\sync.py
```
