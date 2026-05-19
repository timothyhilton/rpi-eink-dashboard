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

TEST_MODE = False

if not TEST_MODE:
    import epaper # pyright: ignore[reportMissingImports]
    epd = epaper.epaper("epd3in7").EPD()

secrets = json.load(open("secrets.json"))

def get_weather_data():
    response = requests.get(f"https://api.weatherapi.com/v1/forecast.json?key={secrets['weather-key']}&q=Brisbane&aqi=no&days=1")
    response.raise_for_status()
    data = response.json()
    feelslike = data["current"]["feelslike_c"]
    maxtemp = data["forecast"]["forecastday"][0]["day"]["maxtemp_c"]
    mintemp = data["forecast"]["forecastday"][0]["day"]["mintemp_c"]
    condition = data["current"]["condition"]["text"]
    chance_of_rain = data["forecast"]["forecastday"][0]["day"]["daily_chance_of_rain"]
    return feelslike, maxtemp, mintemp, condition, chance_of_rain

def get_calendar_data():
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
    return events

def prepare_image(image_path, events, feelslike, maxtemp, mintemp, condition, chance_of_rain):
    #prepare base image
    img = Image.open(image_path).convert("RGBA").rotate(270, expand=True)
    img = ImageOps.pad(img, (280, 480), color="white", centering=(0.5, 1.0))

    # setup draw stuff
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=20)

    # weather
    text = f'FL: {feelslike} | Lw: {mintemp} | Hgh: {maxtemp}\n{chance_of_rain}% | {condition}'
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

        cal_text += f'{event["summary"]}\n{time} |{start_humanized}\n'

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

    lowest_box = cal_box[3]
    return img, lowest_box

# THIS FUNCTION WAS WRITTEN BY AI
def display_1gray_partial(epd, img, box):
    """Update a full-width 1-bit strip from the top of the display."""
    y1 = min(epd.height, box[3])
    image = epd.getbuffer(img.convert("1"))
    row_bytes = int(epd.width / 8)

    epd.send_command(0x44)
    epd.send_data(0x00)
    epd.send_data(0x00)
    epd.send_data((epd.width - 1) & 0xFF)
    epd.send_data(((epd.width - 1) >> 8) & 0x03)

    epd.send_command(0x45)
    epd.send_data(0x00)
    epd.send_data(0x00)
    epd.send_data((y1 - 1) & 0xFF)
    epd.send_data(((y1 - 1) >> 8) & 0x03)

    epd.send_command(0x4E)
    epd.send_data(0x00)
    epd.send_data(0x00)
    epd.send_command(0x4F)
    epd.send_data(0x00)
    epd.send_data(0x00)

    epd.send_command(0x24)
    for i in range(row_bytes * y1):
        epd.send_data(image[i])

    epd.load_lut(epd.lut_1Gray_DU)
    epd.send_command(0x20)
    epd.ReadBusy()

#save or display image
if TEST_MODE:
    feelslike, maxtemp, mintemp, condition, chance_of_rain = get_weather_data()
    events = get_calendar_data()

    img, _ = prepare_image("./images/test.png", events, feelslike, maxtemp, mintemp, condition, chance_of_rain)

    out_path = "./images/out/out.png"
    img.save(out_path)
    print(f"saved preview to {out_path}")
    exit()




def main():
    tick = 0
    while True:
        # prepare data
        feelslike, maxtemp, mintemp, condition, chance_of_rain = get_weather_data()
        events = get_calendar_data()

        # draw image
        img, lowest_box = prepare_image("./images/test.png", events, feelslike, maxtemp, mintemp, condition, chance_of_rain)

        # display image
        if tick % 20 == 0:
            # full refresh
            epd.init(0)
            epd.display_4Gray(epd.getbuffer_4Gray(img))
            epd.init(1)
        else:
            # partial refresh
            display_1gray_partial(epd, img, (0, 0, 280, lowest_box))

        time.sleep(2)

        tick += 1
main()