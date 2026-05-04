import epaper
from PIL import Image, ImageDraw, ImageFont

# waveshare-epaper nests drivers under `epaper` (there is no top-level `waveshare_epd` package).
epd = epaper.epaper("epd3in7").EPD()
epd.init(0)          # 0 = 1-bit (black & white) mode
epd.Clear(0xFF, 0)   # clear to white

# Create a blank white image (rotated to portrait: 280 wide, 480 tall)
image = Image.new('1', (epd.width, epd.height), 255)
draw = ImageDraw.Draw(image)

# Draw stuff
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 24)
draw.text((10, 20), 'Hello, world!', font=font, fill=0)
draw.text((10, 60), 'Second line', font=font, fill=0)
draw.rectangle((10, 100, 270, 200), outline=0)

# Push to screen
epd.display_1Gray(epd.getbuffer(image))

# Sleep
epd.sleep()