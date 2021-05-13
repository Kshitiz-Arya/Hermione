from PIL import Image, ImageDraw

img = Image.new("RGB", (200, 50), color=None)

img2 = ImageDraw.Draw(img)
colours = (65280, 16711680, 16776960, 65535)

pos = 0

for c in colours:

    hex="%06x" % c    # print(r, g, b)
    img2.rectangle([pos, 0, 50+pos, 50+pos], fill=f"#{hex}", outline='white')
    pos += 50

img.save('colours.png', "PNG", dpi=(3100,3100))
