import time
from epaper_dithering import dither_image, ColorScheme, DitherMode
from PIL import Image, ImageDraw, ImageFont, ImageOps
import json
import requests
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import arrow

TEST_MODE = True

if not TEST_MODE:
    import epaper # pyright: ignore[reportMissingImports]
    epd = epaper.epaper("epd3in7").EPD()

secrets = json.load(open("secrets.json"))

#prepare base image
img = Image.open("./images/test2.png").convert("RGBA").rotate(270, expand=True)
img = ImageOps.pad(img, (280, 480), color="white")

# get weather data
response = requests.get(f"https://api.weatherapi.com/v1/forecast.json?key={secrets['weather-key']}&q=Brisbane&aqi=no&days=1")
response.raise_for_status()
data = response.json()
feelslike_c = data["current"]["feelslike_c"]
maxtemp_c = data["forecast"]["forecastday"][0]["day"]["maxtemp_c"]
mintemp_c = data["forecast"]["forecastday"][0]["day"]["mintemp_c"]
condition = data["current"]["condition"]["text"]
chance_of_rain = data["forecast"]["forecastday"][0]["day"]["daily_chance_of_rain"]

#get calendar data
creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/calendar.readonly"])
service = build("calendar", "v3", credentials=creds)
events_result = (
    service.events()
    .list(
        calendarId="primary",
        timeMin=arrow.now().isoformat(),
        timeMax=arrow.now().shift(hours=24).isoformat(),
        maxResults=10,
        singleEvents=True,
        orderBy="startTime",
    )
    .execute()
)
events = events_result.get("items", [])

# setup draw stuff
draw = ImageDraw.Draw(img)
font = ImageFont.load_default(size=20)

 # weather
text = f'FL: {feelslike_c} | Lw: {mintemp_c} | Hgh: {maxtemp_c}\n{chance_of_rain}% | {condition}'
textCoords = (2, -2)
box = draw.textbbox(textCoords, text, font=font)
box = (box[0]-1, box[1]-3, box[2]+1, box[3]+1)
 # calendar
# cal_text = f'Happening today:\n'
cal_text = ''
for event in events:
    start = arrow.get(
        event["start"].get("dateTime", event["start"].get("date"))
    )

    time = "All Day"
    if "T" in start.isoformat():
        time = start.format("h:mmA")

    start_humanized = arrow.get(start).humanize()

    cal_text += f'{time} | {event["summary"]}\n{start_humanized}\n'

cal_textCoords = (2, 47)
cal_box = draw.textbbox(cal_textCoords, cal_text, font=ImageFont.load_default(size=18))
cal_box = (cal_box[0]-1, cal_box[1]-3, cal_box[2]+1, cal_box[3]+1)


# draw stuff
draw.rectangle(box, outline="black", fill="white")
draw.text(textCoords, text, font=font, fill="black")

draw.rectangle(cal_box, outline="black", fill="white")
draw.text(cal_textCoords, cal_text, font=ImageFont.load_default(size=18), fill="black")

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
epd.Clear(0xFF, 0)
epd.display_4Gray(epd.getbuffer_4Gray(img))