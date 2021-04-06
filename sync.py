import asyncio
import signal
from bleak import BleakClient
from bleak import discover
from huelib.HueDevice import HueDevice
from PIL import ImageGrab, Image

SKIP = 10
Y_OFFSET = 50
X_OFFSET = 50
RUNNING = True
RUNNING_TASK = None


def signalHandler(sig, frame):
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

# Create loop
loop = asyncio.get_event_loop()
    
# Start
RUNNING_TASK = loop.run_until_complete(start())