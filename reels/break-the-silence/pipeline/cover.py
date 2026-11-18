# Reel cover (1080x1920) in the house style of the earlier Cub covers: a still of Anjali (same skin retouch and
# cinematic grade as the reel) with a white rounded card: "Break The" in charcoal DM Sans Bold and "Silence" in orange
# Playfair Display Italic. Card and face sit inside the 3:4 profile-grid crop (y 240-1680).
#   python cover.py <time in source seconds> out.jpg
import os, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import render as R                 # retouch(), face_box(), grade() from the reel renderer

FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
W, H = 1080, 1920
ORANGE, CHAR, WHITE = (240, 133, 62), (43, 43, 43), (255, 255, 255)
ZOOM, FACE_Y, CARD_CY = 1.45, 1060, 470


def frame(t):
    a = R.ANCH[min(R.ANCH)]
    cw, ch = R.SW / ZOOM, R.SH / ZOOM
    x0 = min(max(a["cx"] - cw / 2, 0), R.SW - cw)
    y0 = min(max(a["cy"] - FACE_Y / H * ch, 0), R.SH - ch)
    ev = lambda v: int(round(v / 2) * 2)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", R.SRC, "-frames:v", "1", "-vf",
                          f"crop={ev(cw)}:{ev(ch)}:{ev(x0)}:{ev(y0)},scale={W}:{H}:flags=lanczos", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True).stdout
    img = np.frombuffer(raw, np.uint8).reshape(H, W, 3).copy()
    img = R.retouch(img, R.face_box(img, -1))
    return Image.fromarray(R.grade(img)).convert("RGBA")


def dm(size, wght=700):
    f = ImageFont.truetype(f"{FD}/DMSans-VF.ttf", size)
    f.set_variation_by_axes([min(40, max(9, size / 2.2)), wght])
    return f


def ink(s, f, fill):
    asc, desc = f.getmetrics()
    im = Image.new("RGBA", (int(f.getlength(s)) + 30, asc + desc + 20), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, 10 + asc), s, font=f, fill=fill + (255,), anchor="ls")
    return im, 10 + asc


def card():
    a, ba = ink("Break The", dm(92), CHAR)
    b, bb = ink("Silence", ImageFont.truetype(f"{FD}/PlayfairDisplay-400i.ttf", 150), ORANGE)
    a = a.crop(a.getchannel("A").getbbox()); b = b.crop(b.getchannel("A").getbbox())
    gap, px, py = 18, 70, 50
    cw = max(a.width, b.width) + 2 * px; chh = a.height + gap + b.height + 2 * py
    s = 3
    box = Image.new("RGBA", (cw * s, chh * s), (0, 0, 0, 0))
    ImageDraw.Draw(box).rounded_rectangle((0, 0, cw * s - 1, chh * s - 1), 38 * s, fill=WHITE + (250,))
    box = box.resize((cw, chh), Image.LANCZOS)
    box.alpha_composite(a, ((cw - a.width) // 2, py)); box.alpha_composite(b, ((cw - b.width) // 2, py + a.height + gap))
    pad = 60
    out = Image.new("RGBA", (cw + 2 * pad, chh + 2 * pad), (0, 0, 0, 0))
    m = Image.new("L", out.size, 0); m.paste(box.getchannel("A"), (pad, pad + 10))
    m = m.filter(ImageFilter.GaussianBlur(22)).point(lambda v: v * 70 // 255)
    sh = Image.new("RGBA", out.size, (30, 25, 20, 0)); sh.putalpha(m)
    out.alpha_composite(sh); out.alpha_composite(box, (pad, pad))
    return out


def main():
    t, out = float(sys.argv[1]), sys.argv[2]
    img = frame(t)
    c = card()
    img.alpha_composite(c, ((W - c.width) // 2, CARD_CY - c.height // 2))
    img.convert("RGB").save(out, quality=93, subsampling=0)
    img.convert("RGB").crop((0, 240, 1080, 1680)).resize((540, 720), Image.LANCZOS).save(out.replace(".jpg", "_grid_preview.jpg"), quality=90)
    print("wrote", out)


if __name__ == "__main__":
    main()
