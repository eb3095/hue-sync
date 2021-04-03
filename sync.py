import asyncio
from bleak import BleakClient
from bleak import discover
from huelib.HueDevice import HueDevice
from PIL import ImageGrab, Image

SKIP = 10
Y_OFFSET = 50
X_OFFSET = 50

def getColorSpace():
    image = ImageGrab.grab()
    red = green = blue = 0
    for y in range(Y_OFFSET - 1, image.size[1] - Y_OFFSET, SKIP):
        for x in range(X_OFFSET - 1, image.size[0] - X_OFFSET, SKIP):
            # [R, G, B]
            color = image.getpixel((x, y))
   
            red += color[0]
            green += color[1]
            blue += color[2]
            
    yPixels = image.size[1] - (Y_OFFSET * 2)
    xPixels = image.size[0] - (X_OFFSET * 2)
    pixelCount = (yPixels / SKIP) * (xPixels / SKIP)
    red = (red / pixelCount)
    green = (green / pixelCount)
    blue = (blue / pixelCount)
    
    # Logic above can get iffy due to math
    if red > 255:
        red = 255
    if green > 255:
        green = 255
    if blue > 255:
        blue = 255
        
    return [int(red), int(green), int(blue)]

async def run(device):     
        color = getColorSpace()
        brightness = max(color)
        await device.setColor(color)
        await device.setBrightness(brightness)       
        
async def getDevice():
    for i in range(5):
        devices = await discover()
        for d in devices:
            if "Hue Lamp" in d.name:
                return d.address
        print("No device found, Try: %s" % i)
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
        while True:
            await run(device)
            
            # Roughly 60hz
            await asyncio.sleep(0.0167)


# Create loop
loop = asyncio.get_event_loop()
    
# Start
loop.run_until_complete(start())
