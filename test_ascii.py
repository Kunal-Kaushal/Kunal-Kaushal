import sys
from PIL import Image

ASCII_RAMP = " .,:;i1tfLCG08@#"[::-1]
ASCII_RAMP_LEN = len(ASCII_RAMP)
CHAR_ASPECT_RATIO = 0.55
width = 80

img = Image.open("assets/headshot.jpeg")
aspect = img.height / img.width
height = int(width * aspect * CHAR_ASPECT_RATIO)
img = img.resize((width, height), Image.Resampling.LANCZOS).convert("L")

pixels = list(img.getdata())
for row in range(height):
    chars = []
    for col in range(width):
        brightness = pixels[row * width + col]
        # Invert logic: dark is space, bright is dense
        idx = int(brightness / 256 * ASCII_RAMP_LEN)
        idx = min(idx, ASCII_RAMP_LEN - 1)
        chars.append(ASCII_RAMP[idx])
    print("".join(chars))
