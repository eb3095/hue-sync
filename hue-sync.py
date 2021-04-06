import asyncio
import signal
import sys
import os
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
SKIP = 10
Y_OFFSET = 50
X_OFFSET = 50

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

def signalHandler(sig, frame):
    quitSync()
    
def quitSync():    
    global RUNNING
    RUNNING = False
    if RUNNING_TASK:
        RUNNING_TASK.cancel()
    
def setMode(mode): 
    print("Mode Changed: %s" % mode)
    global MODE, RUNNING_TASK
    MODE = mode
    if RUNNING_TASK:
        RUNNING_TASK.cancel()

def getColorSpace():
    # Screenshot primary screen
    image = ImageGrab.grab()
        
    # Calculate pixel colors
    red = green = blue = 0
    for y in range(Y_OFFSET, image.size[1] - Y_OFFSET, SKIP):
        for x in range(X_OFFSET, image.size[0] - X_OFFSET, SKIP):
            # [R, G, B]
            color = image.getpixel((x, y))
   
            red += color[0]
            green += color[1]
            blue += color[2]
            
    # Calculate pixels
    yPixels = image.size[1] - (Y_OFFSET * 2)
    xPixels = image.size[0] - (X_OFFSET * 2)
    pixelCount = (yPixels / SKIP) * (xPixels / SKIP)
    
    # Calculate avg color
    red = (red / pixelCount)
    green = (green / pixelCount)
    blue = (blue / pixelCount)
        
    return [int(red), int(green), int(blue)]

async def sync(device):     
        # Get values
        color = getColorSpace()
        brightness = max(color)
        
        # Set values
        await device.setColor(color)
        await device.setBrightness(brightness)     
                   
        # Roughly 60hz
        await asyncio.sleep(0.0167)   
        
# Cancelable wait task
async def wait():
    while RUNNING:
        # Wait a second
        await asyncio.sleep(1.0)
        
async def getDevice():
    for i in range(5):
        try:
            devices = await discover()
        except Exception as ex:
            print("Error connecting to device, Try: %s" % (i + 1))
            continue

        for d in devices:
            if "Hue Lamp" in d.name:
                return d.address
            
        print("No device found, Try: %s" % (i + 1))
    return None
    
async def start():   
    global RUNNING_TASK
            
    print("Discovering...")
    address = await getDevice()
    
    if not address:
        print("Device couldn't be found!")
        exit(255)
        
    print("Found: %s" % address)
    
    print("Connecting to device...")
    async with BleakClient(address) as client:
        # Get device obj
        device = HueDevice(client)
        
        print("Powering on...")        
        await device.powerOn()       
        await asyncio.sleep(1.0)
        
        print("Starting loop...")
        while RUNNING:
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
            if MODE != "SYNC":
                RUNNING_TASK = asyncio.ensure_future(wait())
            if MODE == "SYNC":
                RUNNING_TASK = asyncio.ensure_future(sync(device))
            
            # Await the task
            try:
                await RUNNING_TASK
            except asyncio.CancelledError:
                pass
            
            # Clear the task
            RUNNING_TASK = None
            
        # Sig kill happened
        print('Termination detected, ending gracefully!')

# Catch CTRL+C
signal.signal(signal.SIGINT, signalHandler)

# Create app
app = QtWidgets.QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)
widget = QWidget()

# Create tray
createTray(widget)
    
# Loop for asyncio
loop = QEventLoop(app)
asyncio.set_event_loop(loop)

# Start
with loop:
    loop.run_until_complete(start())
