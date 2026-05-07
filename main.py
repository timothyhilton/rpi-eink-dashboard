from epaper_dithering import dither_image, ColorScheme, DitherMode
from PIL import Image, ImageDraw, ImageFont, ImageOps
import json
import requests

TEST_MODE = True

if not TEST_MODE:
    import epaper
    epd = epaper.epaper("epd3in7").EPD()

secrets = json.load(open("secrets.json"))

#prepare base image
img = Image.open("./images/test2.png").convert("RGBA").rotate(270, expand=True)
img = ImageOps.pad(img, (280, 480), color="white")

response = requests.get(f"https://api.weatherapi.com/v1/current.json?key={secrets['api_key']}&q=Brisbane&aqi=no")
response.raise_for_status()
data = response.json()
feelslike_c, condition_text = data["current"]["feelslike_c"], data["current"]["condition"]["text"]

# setup draw stuff
draw = ImageDraw.Draw(img)
font = ImageFont.truetype("fonts/Inter.ttf", size=23)
text = f'temp feels like {feelslike_c}°C\ncondition is {condition_text}'
textCoords = (10, 20)
box = draw.textbbox(textCoords, text, font=font)

# draw stuff
draw.rectangle(box, outline="black", fill="white")
draw.text(textCoords, text, font=font, fill="black")

# dither image
img = dither_image(
    img,
    ColorScheme.GRAYSCALE_4,
    mode=DitherMode.STUCKI,
)

#save or display image
if TEST_MODE:
    out_path = "./images/out/out.png"
    img.save(out_path)
    print(f"saved preview to {out_path}")
    exit()

epd.init(0)
epd.display_4Gray(epd.getbuffer_4Gray(img))
epd.sleep()