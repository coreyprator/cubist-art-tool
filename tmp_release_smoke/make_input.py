from PIL import Image, ImageDraw
import os
import sys

out = sys.argv[1]
os.makedirs(os.path.dirname(out), exist_ok=True)
W, H = 256, 256
im = Image.new("RGB", (W, H), "white")
dr = ImageDraw.Draw(im)
dr.rectangle([32, 32, 224, 224], outline="black", width=3)
dr.ellipse([96, 96, 160, 160], fill="red", outline="black")
im.save(out, "PNG")
print("Wrote", out)
