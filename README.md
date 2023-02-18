# hue-sync
Hue LED Strip color syncing for PC.

# Description
This can be used to sync multiple "Hue Lamp" to a PC screen for color syncing. Theres a few
limitations which are strictly based on my personal use case.

This does NOT use the bridge! This is a DIRECT bluetooth connection!

* Only the primary screen is captured
* Only every 10 pixels are computed due to performance (configurable)

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

Alternatively use the EXE in dist/

# Building
There are some issues with building this that needs to be addressed.

Unintall enum34
```
pip uninstall -y enum34
```

You need to use pip 18.1
```
python -m pip install pip==18.1
```

Do these steps BEFORE installing requirements or pyinstall will fail.

# Usage
```
python .\hue-sync.py
```

Alternatively Run the EXE in dist/

# Configuration
The config should be config.json and next to the exe or py file.

```json
{
    "SKIP": 10,
    "Y_OFFSET": 50,
    "X_OFFSET": 50,
    "Devices": {
        "XX:XX:XX:XX:XX:XX": "top",
        "XX:XX:XX:XX:XX:XX": "left",
        "XX:XX:XX:XX:XX:XX": "right",
        "XX:XX:XX:XX:XX:XX": "bottom",
        "XX:XX:XX:XX:XX:XX": "all"
    }
}
```

- Y and X offset are for border ignore. 
- Skip is a perfomance tweak for skipping pixels. 
- If devices is blank all will be used, if defined, only the ones listed
  will be used. The value is the position.
- Valid positions are top, bottom, left, right, and all.
