from PIL import Image, ImageDraw, ImageFont, ImageOps
from pathlib import Path

TEST_MODE = False

if not TEST_MODE:
    import epaper

whiteImage = Image.new("RGBA", (280, 480), "white")
pictureImage = Image.open("./images/test.png")
paddedPictureImage = ImageOps.pad(pictureImage, (280, 480), color="white")

img = Image.alpha_composite(whiteImage, paddedPictureImage)

# Draw stuff
draw = ImageDraw.Draw(img)
draw.rectangle((5, 15, 90, 35), outline="black", fill="white")
draw.text((10, 20), 'this is a test', font=ImageFont.load_default(), fill="black")

if TEST_MODE:
    out_path = Path(__file__).resolve().parent / "out.png"
    img.save(out_path)
    print(f"saved preview to {out_path}")
    exit()

epd = epaper.epaper("epd3in7").EPD()
epd.init(1)
epd.display_4Gray(epd.getbuffer_4Gray(img))
epd.sleep()
