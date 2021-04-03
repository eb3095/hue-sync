from bleak import BleakClient

# Credit: https://gist.github.com/shinyquagsire23/f7907fdf6b470200702e75a30135caf3
LIGHT_CHARACTERISTIC = "932c32bd-0002-47a2-835a-a8d455b859dd"
BRIGHTNESS_CHARACTERISTIC = "932c32bd-0003-47a2-835a-a8d455b859dd"
COLOR_CHARACTERISTIC = "932c32bd-0005-47a2-835a-a8d455b859dd"

# Maybe in the future...
TEMP_CHARACTERISTIC = "932c32bd-0004-47a2-835a-a8d455b859dd"


# Credit: https://github.com/npaun/philble/blob/master/philble/client.py
def convertRGB(rgb):
    scale = 0xff
    adjusted = [max(1, chan) for chan in rgb]
    total = sum(adjusted)
    adjusted = [int(round(chan/total * scale)) for chan in adjusted]
    return [0x1, adjusted[0], adjusted[2], adjusted[1]]

class HueDevice:
    client = None
    
    def __init__(self, client):
        self.client = client
        
    async def setColor(self, color):
        await self.client.write_gatt_char(
            COLOR_CHARACTERISTIC,
            bytearray(
                convertRGB(color)
            )
        )
        
    async def setBrightness(self, brightness):
        await self.client.write_gatt_char(
            BRIGHTNESS_CHARACTERISTIC,
            bytearray(
                [
                    brightness
                ]
            )
        )
        
    async def powerOn(self):
        await self.client.write_gatt_char(LIGHT_CHARACTERISTIC, b"\x01")
        
    async def powerOff(self):
        await self.client.write_gatt_char(LIGHT_CHARACTERISTIC, b"\x00")