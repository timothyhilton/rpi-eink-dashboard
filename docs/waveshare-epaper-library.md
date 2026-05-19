# Waveshare e-Paper Python Library

This project uses the `waveshare-epaper` package from PyPI:

```python
import epaper

epd = epaper.epaper("epd3in7").EPD()
```

That PyPI package is a Python packaging wrapper around Waveshare's official
`e-Paper` repository. The display in this project is the Waveshare 3.7 inch
e-Paper HAT, whose driver module is `epd3in7`.

## Sources

- PyPI wrapper: https://pypi.org/project/waveshare-epaper/
- Wrapper repository: https://github.com/yskoht/waveshare-epaper
- Manufacturer source repository: https://github.com/waveshare/e-Paper
- `epd3in7.py` driver: https://github.com/waveshare/e-Paper/blob/master/RaspberryPi_JetsonNano/python/lib/waveshare_epd/epd3in7.py
- 3.7 inch HAT manual/wiki: https://www.waveshare.com/wiki/3.7inch_e-Paper_HAT_Manual

## What Is Installed

`requirements.txt` installs:

```text
waveshare-epaper>=1.4,<2
```

This provides the top-level `epaper` import. The wrapper lets code select a
driver module by model name:

```python
import epaper

print(epaper.modules())
epd3in7 = epaper.epaper("epd3in7")
epd = epd3in7.EPD()
```

The wrapper mirrors the underlying Waveshare driver modules, so once you call
`epaper.epaper("epd3in7")`, the API is the same as using Waveshare's
`waveshare_epd.epd3in7` module directly.

## Runtime Environment

The driver is for Raspberry Pi / Jetson Nano style GPIO and SPI environments.
It is not expected to import cleanly on macOS because it imports hardware
libraries such as `spidev`, `gpiozero`, `lgpio`, or platform GPIO bindings.

For this repo, develop image-generation logic locally, then run on the Pi with:

```sh
./dev.sh
```

## Hardware Summary

For the Waveshare 3.7 inch e-Paper HAT:

| Property | Value |
| --- | --- |
| Driver module | `epd3in7` |
| Resolution | `480 x 280` pixels |
| Display colors | Black and white |
| Grayscale | 4 levels |
| Interface | SPI |
| SPI mode | Mode 0 |
| Typical full refresh | About 3 seconds |
| Operating voltage | 3.3V panel logic; newer driver boards support 3.3V and 5V environments |
| Operating temperature | 0 to 55 C |

The Waveshare driver exposes the logical display dimensions as:

```python
epd.width   # 280
epd.height  # 480
```

This is why this project prepares images at `(280, 480)` even though the panel
specification is commonly written as `480 x 280`.

## Raspberry Pi Pin Mapping

The driver uses BCM pin numbering:

| e-Paper signal | Raspberry Pi BCM | Header pin |
| --- | ---: | ---: |
| VCC | 3.3V power | 1 |
| GND | GND | 6 |
| DIN / MOSI | GPIO 10 | 19 |
| CLK / SCLK | GPIO 11 | 23 |
| CS | GPIO 8 / CE0 | 24 |
| DC | GPIO 25 | 22 |
| RST | GPIO 17 | 11 |
| BUSY | GPIO 24 | 18 |
| PWR | GPIO 18 | 12 |

The Python `epdconfig.py` layer opens SPI bus `0`, device `0`, sets SPI speed
to 4 MHz, and uses SPI mode `0b00`.

## Manufacturer Precautions

Waveshare's manual calls out a few panel-care rules that matter for dashboard
code:

- Do not partial-refresh indefinitely. After several partial refreshes, do a
  full refresh.
- Do not leave the panel powered in an active high-voltage state for long idle
  periods. Put it to sleep or power it off when it is not refreshing.
- After `sleep()`, image data sent to the display is ignored until the driver is
  initialized again.
- Waveshare recommends a refresh interval of at least 180 seconds for normal
  use, plus at least one refresh every 24 hours if the display remains in use.
- Clear the screen before long-term storage.
- If image data displays incorrectly, check width/height first.
- The FPC cable and glass are fragile; avoid repeated bending, pressure, or
  impacts.

## Install On Raspberry Pi

This repo already lists the package requirements, so the usual project install
path should be:

```sh
python3 -m pip install -r requirements.txt
```

If installing from the manufacturer repository instead of the PyPI wrapper:

```sh
git clone https://github.com/waveshare/e-Paper.git
cd e-Paper/RaspberryPi_JetsonNano/python
sudo python3 setup.py install
```

Waveshare's wiki also lists these base dependencies:

```sh
sudo apt-get update
sudo apt-get install python3-pip python3-pil python3-numpy
sudo pip3 install spidev
sudo apt install python3-gpiozero
```

This repo also pins `gpiozero` and `lgpio` because the wrapper does not declare
all hardware dependencies itself.

## Enable SPI

On the Raspberry Pi:

```sh
sudo raspi-config
```

Then enable SPI through:

```text
Interface Options -> SPI
```

You can sanity-check the SPI device with:

```sh
ls /dev/spi*
```

Expected default device:

```text
/dev/spidev0.0
```

## Basic Usage

Minimal 4-gray full-screen display:

```python
from PIL import Image
import epaper

epd = epaper.epaper("epd3in7").EPD()

image = Image.open("image.png").convert("L")
image = image.resize((epd.width, epd.height))

epd.init(0)
epd.display_4Gray(epd.getbuffer_4Gray(image))
epd.sleep()
```

Minimal 1-bit display:

```python
from PIL import Image
import epaper

epd = epaper.epaper("epd3in7").EPD()

image = Image.open("image.png").convert("1")
image = image.resize((epd.width, epd.height))

epd.init(1)
epd.display_1Gray(epd.getbuffer(image))
epd.sleep()
```

Clear the panel:

```python
epd.init(0)
epd.Clear(0xFF, 0)

epd.init(1)
epd.Clear(0xFF, 1)
```

## Driver Object

Create an EPD object:

```python
epd = epaper.epaper("epd3in7").EPD()
```

Important public attributes:

| Attribute | Meaning |
| --- | --- |
| `width` | Logical image width. For `epd3in7`, `280`. |
| `height` | Logical image height. For `epd3in7`, `480`. |
| `reset_pin` | GPIO pin used for hardware reset. |
| `dc_pin` | GPIO pin used to select command vs data. |
| `busy_pin` | GPIO pin read while waiting for the panel controller. |
| `cs_pin` | SPI chip-select pin. |
| `GRAY1` | Driver grayscale constant for white. |
| `GRAY2` | Driver grayscale constant for light gray. |
| `GRAY3` | Driver grayscale constant for dark gray. |
| `GRAY4` | Driver grayscale constant for black. |
| `lut_4Gray_GC` | Lookup table for 4-gray full refresh. |
| `lut_1Gray_GC` | Lookup table for 1-bit global refresh. |
| `lut_1Gray_DU` | Lookup table used by the project for partial/direct 1-bit update. |
| `lut_1Gray_A2` | Lookup table used by `display_1Gray`. |

## Public Methods

### `init(mode)`

Initializes GPIO, SPI, resets the display controller, configures the controller,
and prepares the panel for either 4-gray or 1-bit operation.

```python
epd.init(0)  # 4-gray mode
epd.init(1)  # 1-bit mode
```

Returns `0` on success and `-1` if hardware initialization fails.

Use `mode=0` before:

```python
epd.display_4Gray(...)
epd.Clear(..., 0)
```

Use `mode=1` before:

```python
epd.display_1Gray(...)
epd.Clear(..., 1)
```

This repo does an initial full 4-gray draw and then switches to 1-bit mode for
fast updates:

```python
epd.init(0)
epd.display_4Gray(epd.getbuffer_4Gray(img))
epd.init(1)
```

### `getbuffer(image)`

Converts a Pillow image to the 1-bit packed buffer expected by the display.

```python
buffer = epd.getbuffer(image)
```

Input:

- A `PIL.Image.Image`.
- Best supplied as mode `"1"` or converted by the driver to mode `"1"`.
- Size must be either `(epd.width, epd.height)` or `(epd.height, epd.width)`.

Output:

- A list-like byte buffer.
- One bit per pixel.
- White pixels are represented by `1`, black pixels by `0`.

Orientation behavior:

- If image size is `(280, 480)`, the driver treats it as vertical/native.
- If image size is `(480, 280)`, the driver rotates/maps it into the display
  buffer.

### `getbuffer_4Gray(image)`

Converts a Pillow image to the packed 4-gray buffer expected by
`display_4Gray`.

```python
buffer = epd.getbuffer_4Gray(image)
```

Input:

- A `PIL.Image.Image`.
- The driver converts it to mode `"L"`.
- Size must be either `(epd.width, epd.height)` or `(epd.height, epd.width)`.

Output:

- A packed buffer with 2 bits per pixel.
- Four pixels are packed into each byte.
- The 3.7 inch panel uses two internal RAM planes, so `display_4Gray` further
  splits this buffer into command `0x24` and command `0x26` writes.

Useful grayscale levels:

| Intended tone | Approximate input value |
| --- | ---: |
| Black | `0x00` |
| Dark gray | `0x40` |
| Light gray | `0x80` |
| White | `0xC0` / high values |

If a source image has arbitrary grayscale values, dithering first gives better
results. This repo uses `epaper-dithering` for that.

### `display_4Gray(image_buffer)`

Writes a full 4-gray framebuffer and triggers a refresh:

```python
epd.init(0)
epd.display_4Gray(epd.getbuffer_4Gray(image))
```

Notes:

- Requires `init(0)` for correct 4-gray setup.
- Performs a full panel update.
- Sends data to both the black/white and gray RAM planes.
- Loads the 4-gray lookup table.
- Sends display update command `0x20` and waits for `BUSY` to release.

Use this for:

- Startup.
- Periodic full refreshes.
- Any image where grayscale quality matters.

### `display_1Gray(image_buffer)`

Writes a full 1-bit framebuffer and triggers a refresh:

```python
epd.init(1)
epd.display_1Gray(epd.getbuffer(image))
```

Notes:

- Requires `init(1)` for correct 1-bit setup.
- Uses command `0x24` for display RAM.
- Loads `lut_1Gray_A2`.
- Triggers the display update and waits for `BUSY`.

Use this for:

- Monochrome full-screen updates.
- Fast black/white content after a full refresh.

### `Clear(color, mode)`

Fills the panel RAM and refreshes the panel.

```python
epd.Clear(0xFF, 0)  # clear in 4-gray mode
epd.Clear(0xFF, 1)  # clear in 1-bit mode
```

Parameters:

| Parameter | Meaning |
| --- | --- |
| `color` | Present in the signature, but the driver implementation clears with `0xFF`. |
| `mode` | `0` for 4-gray clear, `1` for 1-bit clear. |

The method writes all-white data to command `0x24`. In 4-gray mode it also
writes all-white data to command `0x26`.

### `sleep()`

Puts the panel controller into deep sleep and releases the hardware interface:

```python
epd.sleep()
```

The driver sends command `0x10`, data `0x03`, delays, and then calls
`epdconfig.module_exit()`.

Call `init(...)` again before displaying after sleep.

## Low-Level Methods

These are exposed on the `EPD` object. Application code usually should not need
them, but this project uses them for a custom partial update helper.

### `reset()`

Toggles the reset pin high/low/high with delays. Called by `init(...)`.

### `send_command(command)`

Sends one command byte over SPI with the DC pin low:

```python
epd.send_command(0x24)
```

### `send_data(data)`

Sends one data byte over SPI with the DC pin high:

```python
epd.send_data(0xFF)
```

### `send_data2(data)`

Sends a larger buffer over SPI with the DC pin high:

```python
epd.send_data2(buffer)
```

### `ReadBusy()`

Blocks until the `BUSY` pin reports the controller is idle. In this driver,
`BUSY == 1` means busy and `BUSY == 0` means idle.

### `load_lut(lut)`

Writes a waveform lookup table to the controller:

```python
epd.load_lut(epd.lut_1Gray_DU)
```

This is needed for custom update modes. The normal display methods call it
internally.

## Partial Update Notes

The upstream `epd3in7` Python module does not expose a nice high-level
`display_partial(...)` API for this display. This repo has a custom helper in
`main.py`:

```python
display_1gray_partial(epd, img, box)
```

The helper performs a top-of-screen 1-bit partial update by:

1. Converting the image to a 1-bit display buffer with `epd.getbuffer(...)`.
2. Setting the X RAM window with command `0x44`.
3. Setting the Y RAM window with command `0x45`.
4. Moving the RAM cursor with commands `0x4E` and `0x4F`.
5. Writing the selected bytes to command `0x24`.
6. Loading `epd.lut_1Gray_DU`.
7. Triggering update command `0x20`.
8. Waiting for `BUSY` to release.

Important constraints:

- It updates from the top of the panel down to `box[3]`.
- It assumes a full-width X range.
- It assumes 1-bit mode, so call `epd.init(1)` before the loop.
- Do an occasional full refresh with `display_4Gray` or `display_1Gray`.

Waveshare warns that displays with partial refresh support should not be
partially refreshed forever. After several partial refreshes, do a full refresh
to avoid abnormal display artifacts.

## Image Preparation

Use Pillow to prepare an image at the logical driver size:

```python
from PIL import Image, ImageOps

img = Image.open("source.png").convert("RGBA")
img = ImageOps.pad(img, (280, 480), color="white")
```

For 4-gray output:

```python
img = img.convert("L")
buffer = epd.getbuffer_4Gray(img)
epd.display_4Gray(buffer)
```

For 1-bit output:

```python
img = img.convert("1")
buffer = epd.getbuffer(img)
epd.display_1Gray(buffer)
```

This repo currently dithers to a 4-level grayscale scheme:

```python
from epaper_dithering import dither_image, ColorScheme, DitherMode

img = dither_image(
    img,
    ColorScheme.GRAYSCALE_4,
    mode=DitherMode.STUCKI,
)
```

## Recommended Refresh Pattern For This Project

The dashboard has a static-ish background plus changing weather/calendar data.
A good pattern is:

```python
epd.init(0)
epd.display_4Gray(epd.getbuffer_4Gray(full_image))
epd.init(1)

partial_count = 0

while True:
    image, lowest_box = get_data_and_prepare_image()
    display_1gray_partial(epd, image, (0, 0, epd.width, lowest_box))
    partial_count += 1

    if partial_count >= 20:
        epd.init(0)
        epd.display_4Gray(epd.getbuffer_4Gray(image))
        epd.init(1)
        partial_count = 0
```

Adjust the `20` based on observed ghosting. E-paper behavior depends on
temperature, update frequency, and image contrast.

## Troubleshooting

### Import Fails On macOS

Expected. The Waveshare library imports Pi hardware modules.

Use `TEST_MODE = True` for local image preview, or run on the Pi through
`./dev.sh`.

### `ModuleNotFoundError: spidev`

Install on the Pi:

```sh
sudo pip3 install spidev
```

### GPIO Errors

Install GPIO dependencies:

```sh
sudo apt install python3-gpiozero
python3 -m pip install gpiozero lgpio
```

### No `/dev/spidev0.0`

Enable SPI with `raspi-config`, then reboot if needed.

### Nothing Updates

Check:

- The HAT is seated or wired correctly.
- SPI is enabled.
- The display model is exactly `epd3in7`.
- The image size is `(280, 480)` or `(480, 280)`.
- The code calls `epd.init(...)` before display calls.
- The code waits for `BUSY` by using normal display methods or calling
  `ReadBusy()` after custom low-level updates.

### Wrong Orientation

The driver accepts both `(280, 480)` and `(480, 280)`, but maps them
differently. In this repo, normalize to `(280, 480)` before calling
`getbuffer(...)` or `getbuffer_4Gray(...)`.

### Ghosting Or Dirty Partial Updates

Do a full refresh periodically:

```python
epd.init(0)
epd.display_4Gray(epd.getbuffer_4Gray(image))
epd.init(1)
```

Partial update loops are convenient, but e-paper panels need full refreshes to
clean up accumulated artifacts.

## Quick API Reference

```python
import epaper

epaper.modules()                 # list supported model module names
epaper.epaper("epd3in7")          # return the epd3in7 module

epd = epaper.epaper("epd3in7").EPD()

epd.width                         # 280
epd.height                        # 480

epd.init(0)                       # initialize for 4-gray mode
epd.init(1)                       # initialize for 1-bit mode

epd.getbuffer(image)              # PIL image -> 1-bit display buffer
epd.getbuffer_4Gray(image)        # PIL image -> 4-gray display buffer

epd.display_1Gray(buffer)         # full-screen 1-bit update
epd.display_4Gray(buffer)         # full-screen 4-gray update

epd.Clear(0xFF, 0)                # clear in 4-gray mode
epd.Clear(0xFF, 1)                # clear in 1-bit mode
epd.sleep()                       # deep sleep and release hardware

epd.send_command(command)         # low-level command byte
epd.send_data(data)               # low-level data byte
epd.send_data2(buffer)            # low-level bulk data write
epd.load_lut(lut)                 # low-level waveform table write
epd.ReadBusy()                    # wait for controller idle
```
