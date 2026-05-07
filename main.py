from epaper_dithering import dither_image, ColorScheme, DitherMode
from PIL import Image, ImageDraw, ImageFont, ImageOps
from pathlib import Path
import requests

TEST_MODE = False

if not TEST_MODE:
    import epaper

epd = epaper.epaper("epd3in7").EPD()

#prepare base image
img = Image.new("RGBA", (280, 480), "white")
pictureImage = ImageOps.contain(Image.open("./images/test.png").convert("RGBA"), img.size)
img.alpha_composite(
    pictureImage,
    ((img.width - pictureImage.width) // 2, (img.height - pictureImage.height) // 2),
)

# get weather data
response = requests.get("https://api.weatherapi.com/v1/current.json?key=a494018a61404a80b0574408260902&q=Brisbane&aqi=no")
response.raise_for_status()
data = response.json()
feelslike_c, condition_text = data["current"]["feelslike_c"], data["current"]["condition"]["text"]

# Draw stuff
draw = ImageDraw.Draw(img)
font = ImageFont.truetype("fonts/Inter.ttf", size=23)
text = f'temp feels like {feelslike_c}°C \ncondition is {condition_text}'
text_x, text_y = 10, 20
# Get the bounding box of the text
box = draw.textbbox((text_x, text_y), text, font=font)
draw.rectangle(box, outline="black", fill="white")
draw.text((text_x, text_y), text, font=font, fill="black")

# dither image
img = dither_image(
    img,
    ColorScheme.GRAYSCALE_4,
    mode=DitherMode.FLOYD_STEINBERG,
)

#save or display image
if TEST_MODE:
    out_path = Path(__file__).resolve().parent / "out.png"
    img.save(out_path)
    print(f"saved preview to {out_path}")
    exit()

epd.init(0)
epd.display_4Gray(epd.getbuffer_4Gray(img))
epd.sleep()