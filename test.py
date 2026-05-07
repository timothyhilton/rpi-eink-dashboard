from epaper_dithering import ColorScheme, DitherMode, dither_image
from PIL import Image, ImageDraw, ImageFont, ImageOps
from pathlib import Path

# When True, skip the e-paper hardware and just save the rendered image to
# `out.png` so we can iterate on the look without a Pi/EPD attached.
TEST_MODE = True

if not TEST_MODE:
    import epaper


def prepare_image(path: str | Path) -> Image.Image:

    size = (280, 480)

    img = Image.open(path).convert("L").transpose(Image.Transpose.ROTATE_90)
    img = ImageOps.pad(img, size, method=Image.LANCZOS, color=255)
    img = ImageOps.autocontrast(img, cutoff=1)

    img = img.point(bytes(int(round(255.0 * (v / 255.0) ** (4/3))) for v in range(256)))

    return dither_image(
        img,
        ColorScheme.GRAYSCALE_4,
        mode=DitherMode.ORDERED,
    ).convert("L")


photo = prepare_image("./images/test.png")
photo = photo.transpose(Image.Transpose.ROTATE_180)

# Draw stuff
draw = ImageDraw.Draw(photo)
font = ImageFont.load_default()
draw.rectangle((5, 15, 90, 35), outline=0, fill=0xff)
draw.text((10, 20), 'i love my keiroo', font=font, fill=0)

if TEST_MODE:
    out_path = Path(__file__).resolve().parent / "out.png"
    photo.save(out_path)
    print(f"saved preview to {out_path}")
    exit()

epd = epaper.epaper("epd3in7").EPD()
epd.init(1)
epd.display_4Gray(epd.getbuffer_4Gray(photo))
epd.sleep()
