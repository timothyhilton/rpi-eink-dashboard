import time
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

# get weather data
response = requests.get(f"https://api.weatherapi.com/v1/forecast.json?key={secrets['api_key']}&q=Brisbane&aqi=no&days=1")
response.raise_for_status()
data = response.json()
feelslike_c = data["current"]["feelslike_c"]
maxtemp_c = data["forecast"]["forecastday"][0]["day"]["maxtemp_c"]
mintemp_c = data["forecast"]["forecastday"][0]["day"]["mintemp_c"]
condition = data["current"]["condition"]["text"]
chance_of_rain = data["forecast"]["forecastday"][0]["day"]["daily_chance_of_rain"]

# setup draw stuff
draw = ImageDraw.Draw(img)
font = ImageFont.load_default(size=20)
text = f'FL: {feelslike_c}, L:{mintemp_c}, H:{maxtemp_c}\n{chance_of_rain}% | {condition}'
textCoords = (2, -2)
box = draw.textbbox(textCoords, text, font=font)
box = (box[0]-1, box[1]-3, box[2]+1, box[3]+1)

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