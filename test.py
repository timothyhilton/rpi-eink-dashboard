from pathlib import Path

import epaper
from PIL import Image, ImageDraw, ImageFont, ImageOps
import time


# The four exact gray bytes the Waveshare epd3in7 4-gray driver checks for.
_LEVELS = (0x00, 0x80, 0xC0, 0xFF)
# 8x8 Bayer matrix, normalised to [-0.5, +0.5).
_BAYER8 = [
    [ 0, 32,  8, 40,  2, 34, 10, 42],
    [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44,  4, 36, 14, 46,  6, 38],
    [60, 28, 52, 20, 62, 30, 54, 22],
    [ 3, 35, 11, 43,  1, 33,  9, 41],
    [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47,  7, 39, 13, 45,  5, 37],
    [63, 31, 55, 23, 61, 29, 53, 21],
]


def _snap(v: int) -> int:
    """Snap an int 0..255 to the nearest of the four EPD gray bytes."""
    if v < 0x40: return 0x00
    if v < 0xA0: return 0x80
    if v < 0xE0: return 0xC0
    return 0xFF


def load_4gray(
    path: str | Path,
    size: tuple[int, int],
    dither: str = "fs",
    autocontrast: bool = True,
    rotate: int = 90,
    brightness: float = 1,
    contrast: float = 1,
    gamma: float = 0.75,
) -> Image.Image:
    """Load an image and quantize it to the 4 shades of gray the EPD supports.

    Scales the image to fit `size` (preserving aspect ratio, padded with white),
    optionally stretches contrast to fill the 0..255 range, then quantizes to
    {0x00, 0x80, 0xC0, 0xFF}. Returns an 'L' mode image.

    `dither`:
        "none"  - clean nearest-neighbour banding (no noise, looks posterized).
        "bayer" - ordered 8x8 dithering (default, regular pattern, no noise).
        "fs"    - Floyd-Steinberg error diffusion (most detail, looks grainy).

    `rotate`: degrees to rotate the source image before scaling. Must be one of
    0, 90, 180, 270. Useful when the source orientation doesn't match the panel.

    Tone controls (applied AFTER autocontrast, BEFORE dithering):
        `brightness`: 1.0 = unchanged. >1 brighter, <1 darker (linear scale).
        `contrast`:   1.0 = unchanged. >1 punchier, <1 flatter (around mid-gray).
        `gamma`:      1.0 = unchanged. <1 lifts midtones (brighter mids),
                      >1 deepens midtones (darker mids). Most useful knob for
                      tuning detail visibility on e-paper, since the four
                      levels (0, 128, 192, 255) are not perceptually uniform.
    """
    if rotate not in (0, 90, 180, 270):
        raise ValueError(f"rotate must be 0, 90, 180, or 270 (got {rotate!r})")

    img = Image.open(path).convert("L")
    if rotate:
        img = img.transpose({
            90: Image.Transpose.ROTATE_90,
            180: Image.Transpose.ROTATE_180,
            270: Image.Transpose.ROTATE_270,
        }[rotate])
    img = ImageOps.pad(img, size, method=Image.LANCZOS, color=255)
    if autocontrast:
        img = ImageOps.autocontrast(img, cutoff=1)

    if brightness != 1.0 or contrast != 1.0 or gamma != 1.0:
        # Single combined LUT: contrast around 128, then brightness, then gamma.
        inv_gamma = 1.0 / gamma
        tone_lut = bytearray(256)
        for v in range(256):
            x = (v - 128) * contrast + 128
            x *= brightness
            x = max(0.0, min(255.0, x))
            x = 255.0 * (x / 255.0) ** inv_gamma
            tone_lut[v] = int(round(max(0.0, min(255.0, x))))
        img = img.point(tone_lut)

    if dither == "none":
        lut = bytes(_snap(v) for v in range(256))
        return img.point(lut)

    if dither == "bayer":
        # Add a per-pixel offset from the Bayer matrix before snapping, so
        # neighbouring pixels round to different levels and visually average.
        # Spread is the gap between adjacent levels; using max gap (0x80) for
        # the [0,0x80] band keeps contrast in shadows.
        w, h = img.size
        src = img.load()
        out = Image.new("L", size)
        dst = out.load()
        for y in range(h):
            row = _BAYER8[y & 7]
            for x in range(w):
                # Offset in [-32, +31], scaled to gap between bands (~64).
                offset = (row[x & 7] - 32) * 2
                dst[x, y] = _snap(max(0, min(255, src[x, y] + offset)))
        return out

    if dither == "fs":
        palette_img = Image.new("P", (1, 1))
        palette_rgb = [c for level in _LEVELS for c in (level, level, level)]
        palette_img.putpalette(palette_rgb + [0] * (256 * 3 - len(palette_rgb)))
        quantized = img.quantize(palette=palette_img, dither=Image.Dither.FLOYDSTEINBERG)
        out = Image.new("L", size)
        out.putdata(bytes(_LEVELS[idx] if idx < 4 else 0xFF for idx in quantized.getdata()))
        return out

    raise ValueError(f"unknown dither mode: {dither!r}")

# waveshare-epaper nests drivers under `epaper` (there is no top-level `waveshare_epd` package).
epd = epaper.epaper("epd3in7").EPD()
epd.init(0)          # 0 = 1-bit (black & white) mode
epd.Clear(0xFF, 0)   # clear to white

# Create a blank white image (rotated to portrait: 280 wide, 480 tall)
image = Image.new('1', (epd.width, epd.height), 255)
draw = ImageDraw.Draw(image)

font = ImageFont.truetype(str(Path(__file__).resolve().parent / "fonts" / "Inter.ttf"), 24)
draw.text((10, 20), "tim lov keiro mor", fill=0, font=font)
draw.text((10, 25), "Second line", fill=0, font=font)
draw.rectangle((10, 100, 270, 200), fill=2,outline=0)

# Push to screen
epd.display_1Gray(epd.getbuffer(image))

time.sleep(3)

# Switch to 4-gray mode (mode 0 is 4Gray, mode 1 is 1Gray in this driver).
# Re-init + clear matches the transition the official Waveshare demo uses;
# without the Clear, the panel can latch into a bad state after a 1-gray push.
epd.init(0)
epd.Clear(0xFF, 0)
photo = load_4gray(Path(__file__).resolve().parent / "images" / "test.png", (epd.width, epd.height))
epd.display_4Gray(epd.getbuffer_4Gray(photo))

epd.sleep()