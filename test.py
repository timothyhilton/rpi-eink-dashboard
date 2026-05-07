from turtle import fillcolor
from PIL import Image, ImageDraw, ImageFont, ImageOps
from pathlib import Path

# When True, skip the e-paper hardware and just save the rendered image to
# `out.png` so we can iterate on the look without a Pi/EPD attached.
TEST_MODE = False

if not TEST_MODE:
    import epaper


def load_4gray(path: str | Path) -> Image.Image:
    """Load an image and quantize it to the 4 shades of gray the EPD supports
    using 8x8 Bayer ordered dithering.

    Rotates 90deg, scales to fit 280x480 (preserving aspect ratio, padded with
    white), stretches contrast, applies a gamma 0.75 lift, then quantizes to
    {0x00, 0x80, 0xC0, 0xFF}. Returns an 'L' mode image.
    """
    size = (280, 480)

    # 8x8 Bayer matrix.
    bayer = [
        [ 0, 32,  8, 40,  2, 34, 10, 42],
        [48, 16, 56, 24, 50, 18, 58, 26],
        [12, 44,  4, 36, 14, 46,  6, 38],
        [60, 28, 52, 20, 62, 30, 54, 22],
        [ 3, 35, 11, 43,  1, 33,  9, 41],
        [51, 19, 59, 27, 49, 17, 57, 25],
        [15, 47,  7, 39, 13, 45,  5, 37],
        [63, 31, 55, 23, 61, 29, 53, 21],
    ]

    def snap(v: int) -> int:
        if v < 0x40: return 0x00
        if v < 0xA0: return 0x80
        if v < 0xE0: return 0xC0
        return 0xFF

    img = Image.open(path).convert("L").transpose(Image.Transpose.ROTATE_90)
    img = ImageOps.pad(img, size, method=Image.LANCZOS, color=255)
    img = ImageOps.autocontrast(img, cutoff=1)

    inv_gamma = 1.0 / 0.75
    tone_lut = bytes(
        int(round(255.0 * (v / 255.0) ** inv_gamma)) for v in range(256)
    )
    img = img.point(tone_lut)

    w, h = img.size
    src = img.load()
    out = Image.new("L", size)
    dst = out.load()
    for y in range(h):
        row = bayer[y & 7]
        for x in range(w):
            offset = (row[x & 7] - 32) * 2
            dst[x, y] = snap(max(0, min(255, src[x, y] + offset)))
    return out


base = load_4gray(Path(__file__).resolve().parent / "images" / "test.png")
base = base.transpose(Image.Transpose.ROTATE_180)

W, H = base.size  # 280 x 480
BOX = (0, 15, W, 45)  # full-width marquee strip
MSG = "i love my keiroo"
GAP = 40  # px between repeats so loop is seamless
font = ImageFont.load_default()

# measure text once
_d = ImageDraw.Draw(base)
tw = int(_d.textlength(MSG, font=font))
bbox = font.getbbox(MSG)
th = bbox[3] - bbox[1]
period = tw + GAP

# pre-render one period tile
strip_h = BOX[3] - BOX[1]
tile = Image.new("L", (period, strip_h), 0xFF)
ImageDraw.Draw(tile).text(
    (0, (strip_h - th) // 2 - bbox[1]), MSG, font=font, fill=0
)


def render(offset: int) -> Image.Image:
    frame = base.copy()
    d = ImageDraw.Draw(frame)
    d.rectangle(BOX, outline=0, fill=0xFF)
    bw = BOX[2] - BOX[0]
    strip = Image.new("L", (bw, strip_h), 0xFF)
    x = -(offset % period)
    while x < bw:
        strip.paste(tile, (x, 0))
        x += period
    frame.paste(strip, (BOX[0], BOX[1]))
    return frame


if TEST_MODE:
    out_dir = Path(__file__).resolve().parent
    n = 0
    for n, off in enumerate(range(0, period, 20)):
        render(off).save(out_dir / f"out_{n:02d}.png")
    print(f"saved {n+1} frames to {out_dir}")
    exit()

epd = epaper.epaper("epd3in7").EPD()
epd.init(0)
STEP = 24  # px per frame; bigger = less chop on slow 4Gray
try:
    off = 0
    while True:
        epd.display_4Gray(epd.getbuffer_4Gray(render(off)))
        off = (off + STEP) % period
finally:
    epd.sleep()
