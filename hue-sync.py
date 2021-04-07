import asyncio
import signal
import sys
import os
import json
import logging
import traceback
from asyncqt import QEventLoop
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from bleak import BleakClient
from bleak import discover
from huelib.HueDevice import HueDevice
from PIL import ImageGrab, Image

#
# CONFIGURATION
#
CONFIG = {    
    "SKIP": 10,
    "Y_OFFSET": 50,
    "X_OFFSET": 50,
    "Devices": []
}

# Runtime
RUNNING = True
RUNNING_TASK = None
MODE = "SYNC"

def createTray(widget):
    tray = QSystemTrayIcon(widget)
    icon = QIcon(getPath("assets/hue-sync.ico"))
    tray.setIcon(icon)
    tray.setVisible(True)
    tray.setToolTip("Hue-Sync")
    
    menu = QMenu(widget)
    
    modes = [
            "Red",
            "Green",
            "Blue",
            "Teal",
            "Purple",
            "Pink",
            "Orange",
            "Yellow",
            "White",
            "Sync",
            "Off"
    ]
    
    for mode in modes:
        def addAction(menu, mode):            
            button = QAction(mode, menu)
            button.triggered.connect(lambda: setMode(mode.upper()))        
            menu.addAction(button)
        addAction(menu, mode)
    
    exitB = QAction("Exit", menu)        
    exitB.triggered.connect(quitSync)        
    menu.addAction(exitB)
    
    tray.setContextMenu(menu)
        
def getPath(relative_path):
    try:
        path = sys._MEIPASS
    except Exception:
        path = os.path.abspath(".")

    return os.path.join(path, relative_path)

def signalHandler():
    quitSync()
    
def quitSync():    
    global RUNNING, RUNNING_TASK
    RUNNING = False
    if RUNNING_TASK:
        RUNNING_TASK.cancel()
        
def log(level, str):
    print("[%s] %s" % (level, str))
    if level == "debug":
        logging.debug(str)
    if level == "info":
        logging.info(str)
    if level == "warning":
        logging.warning(str)
    if level == "error":
        logging.error(str)
        exit(255)
        
def logUncaught(exctype, value, trace):
    # Capture these errors and recover
    # Its from not being able to capture SIGINT on Windows
    if str(exctype) == "<class 'KeyboardInterrupt'>":
        quitSync()
        return
    
    if str(exctype) == "<class 'KeyError'>":
        quitSync()
        return
    
    trace = ''.join(traceback.format_tb(trace))
    log("error", "Error: %s\nValue: %s\nTrace: %s" % (exctype, value, trace))
    
def setMode(mode): 
    log("info", "Mode Changed: %s" % mode)
    global MODE, RUNNING_TASK
    MODE = mode
    if RUNNING_TASK:
        RUNNING_TASK.cancel()

def getColorSpace(pos):
    # Screenshot primary screen
    image = ImageGrab.grab()
        
    # Calculate pixel colors
    red = green = blue = 0
    
    # Calculate based on positions
    yMin = CONFIG['Y_OFFSET']
    yMax = image.size[1] - CONFIG['Y_OFFSET']
    xMin = CONFIG['X_OFFSET']
    xMax = image.size[0] - CONFIG['X_OFFSET']
    
    if pos == "bottom":
        yMin = int(yMax - (yMax * 0.1))
        
    if pos == "top":
        yMax = int(yMin + (yMax * 0.1))
    
    if pos == "right":
        xMin = int(xMax - (xMax * 0.1))
        
    if pos == "left":
        xMax = int(xMin + (xMax * 0.1))
        
    pixels = 0
    for y in range(yMin, yMax, CONFIG['SKIP']):
        for x in range(xMin, xMax, CONFIG['SKIP']):
            # [R, G, B]
            color = image.getpixel((x, y))
   
            red += color[0]
            green += color[1]
            blue += color[2]
            pixels += 1
    
    # Calculate avg color
    red = (red / pixels)
    green = (green / pixels)
    blue = (blue / pixels)
        
    return [int(red), int(green), int(blue)]

async def sync(device):    
        # Get device position
        pos = "all" 
        if "Devices" in CONFIG and device.getAddress() in CONFIG['Devices']:
            pos = CONFIG['Devices'][device.getAddress()]
            
        # Get values
        color = getColorSpace(pos)
        brightness = max(color)
        
        # Set values
        await device.setColor(color)
        await device.setBrightness(brightness)   
        
async def getDevices():
    devs = []
    for i in range(5):
        try:
            devices = await discover()
        except Exception as ex:
            log("info", "Error connecting to device, Try: %s" % (i + 1))
            continue

        for d in devices:
            # Skep devices not in config
            if len(CONFIG["Devices"]) > 0 and d.address not in CONFIG['Devices']:
                continue
            
            if "Hue Lamp" in d.name and d.address not in devs:
                devs.append(d.address)
                
        # Some times devices take a few tries
        await asyncio.sleep(1.0)
        
    # If multi is enabled        
    if len(devs) > 0:
        return devs
        
    log("info", "No device found!")
    return None

async def setDevice(device):
    # Power on if off but set to on
    if MODE != "OFF":
        if not device.isPoweredOn():
            await device.powerOn()
            
    # Set options
    if MODE == "RED":
        color = [255, 0, 0]
    if MODE == "BLUE":
        color = [0, 0, 255]
    if MODE == "GREEN":
        color = [0, 255, 0]
    if MODE == "YELLOW":
        color = [255, 255, 0]
    if MODE == "ORANGE":
        color = [255, 127, 0]
    if MODE == "PURPLE":
        color = [127, 0, 255]
    if MODE == "PINK":
        color = [255, 0, 255]
    if MODE == "TEAL":
        color = [0, 255, 255]
    if MODE == "WHITE":
        color = [255, 255, 255]
        
    # Turn off if set to off
    if MODE == "OFF":
        await device.powerOff()
        
    # Set color and brightness
    if MODE != "OFF" and MODE != "SYNC":
        await device.setColor(color)
        await device.setBrightness(253)
        
    # Set task
    if MODE == "SYNC":
        await sync(device)
        
async def connectToDevices():        
    log("info", "Discovering...")
    addresses = await getDevices()
    
    if not addresses:
        log("info", "Devices couldn't be found!")
        exit(255)
        
    log("info", "Found: %s" % addresses)
    
    log("info", "Connecting to devices...")
    
    devices = []
    for addr in addresses:
        async def doConnect(addr):
            for i in range(5):            
                client = BleakClient(addr)
                device = HueDevice(client)
                try:
                    log("info", "Connecting to: %s" % addr)    
                    await device.connect()
                    log("info", "Powering on...")        
                    await device.powerOn()
                except:
                    log("info", "Failed to connect to: %s, Try: %s" %
                        (device.getAddress(), i))
                    continue                
                return device
            return None
        device = await doConnect(addr)
        if device:
            devices.append(device)
    
    return devices
    
async def start():    
    global RUNNING_TASK            
    devices = await connectToDevices()
    
    if len(devices) < 1:
        log("error", "Failed to connect to any device!")
        
    log("info", "Starting loop...")
    while RUNNING:   
        coroutines = []
        
        for device in devices:
            coroutines.append(setDevice(device))
           
        # Set wait task if not sync        
        if MODE != "SYNC":
            coroutines.append(asyncio.sleep(3600.0))
            
        # Set task
        RUNNING_TASK = asyncio.gather(*coroutines)
        # Await the tasks
        try:
            await RUNNING_TASK
        except asyncio.CancelledError:
            pass
        
        # Clear the task
        RUNNING_TASK = None
        
        # Rest between syncs
        if MODE == "SYNC" and RUNNING:
            # Roughly 60hz
            await asyncio.sleep(0.01) 
            
    # Sig kill happened
    log("info", 'Termination detected, ending gracefully!')
    for device in devices:
        await device.disconnect()


# Set logging
logging.basicConfig(filename='./hue-sync.log', level=logging.INFO)
sys.excepthook = logUncaught

# Parse config
if os.path.exists("config.json"):
    with open('config.json') as file:
        CONFIG.update(json.load(file))
        
# Create app
app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)
widget = QWidget()

# Create tray
createTray(widget)
    
# Loop for asyncio
loop = QEventLoop(app)
asyncio.set_event_loop(loop)

# Catch CTRL+C
try:
    loop.add_signal_handler(signal.SIGINT, signalHandler)
except NotImplementedError:
    # Handle this with log hack
    pass

# Start
with loop:
    loop.run_until_complete(start())
