import asyncio
import signal
import sys
import os
from asyncqt import QEventLoop
from PyQt5 import QtCore, QtGui, QtWidgets
from bleak import BleakClient
from bleak import discover
from huelib.HueDevice import HueDevice
from PIL import ImageGrab, Image

SKIP = 10
Y_OFFSET = 50
X_OFFSET = 50
RUNNING = True
RUNNING_TASK = None

class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        QtWidgets.QSystemTrayIcon.__init__(self, icon, parent)
        menu = QtWidgets.QMenu(parent)
        menu.addAction("Exit")
        self.setContextMenu(menu)
        menu.triggered.connect(self.exit)

    def exit(self):
        quitSync()
        
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

async def run(device):     
        # Get values
        color = getColorSpace()
        brightness = max(color)
        
        # Set values
        await device.setColor(color)
        await device.setBrightness(brightness)     
                   
        # Roughly 60hz
        await asyncio.sleep(0.0167)   
        
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
            # Create the task
            RUNNING_TASK = asyncio.ensure_future(run(device))
            
            # Await the task
            await RUNNING_TASK
            
            # Clear the task
            RUNNING_TASK = None
            
        # Sig kill happened
        print('Termination detected, ending gracefully!')

# Catch CTRL+C
signal.signal(signal.SIGINT, signalHandler)

# Create app
app = QtWidgets.QApplication(sys.argv)
    
# Loop for asyncio
loop = QEventLoop(app)
asyncio.set_event_loop(loop)

# Create tray
widget = QtWidgets.QWidget()
icon = QtGui.QIcon(getPath("assets/hue-sync.ico"))
trayIcon = SystemTrayIcon(icon, widget)
trayIcon.setToolTip("Hue-Sync")
trayIcon.show()

# Start
with loop:
    loop.run_until_complete(start())
