# Reel cover (1080x1920) in the house style of the earlier Cub covers: a warm frame of the speaker, with a white
# rounded card holding the hook. The card's text is charcoal DM Sans Bold, with the key word in orange Playfair
# Display Italic. Everything sits inside the 3:4 profile-grid crop (y 240-1680).
#   python cover.py out.jpg
import os, sys, subprocess
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

WORK = os.environ["WORK"]
FD = os.environ.get("FONT_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts"))
W, H = 1080, 1920
ORANGE, CHAR, WHITE = (240, 133, 62), (43, 43, 43), (255, 255, 255)
SHOT, T = 3, 50.12                 # warm, open smile straight to camera, just after "...time to be a child."
ZOOM, FACE_Y = 1.42, 1030          # face centre placed low enough to leave the wall clear above her for the card
LINE1 = "Do We Allow a Child"
LINE2A, LINE2B = "to Be a ", "Child?"
CARD_CY = 540


def grab(shot, t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", f"{WORK}/shot{shot}.mp4", "-frames:v", "1", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(H, W, 3)


def face(img):
    det = cv2.FaceDetectorYN.create(os.environ.get("MODELS", "models") + "/yunet.onnx", "", (W, H), 0.6, 0.3, 5000)
    _, f = det.detect(cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    r = max(f, key=lambda r: r[-1] * r[2])
    return r[0] + r[2] / 2, r[1] + r[3] / 2


def photo():
    src = grab(SHOT, T)
    cx, cy = face(src)
    ww, wh = W / ZOOM, H / ZOOM
    x0 = min(max(cx - ww / 2, 0), W - ww)
    y0 = min(max(cy - FACE_Y / ZOOM, 0), H - wh)
    M = np.array([[ZOOM, 0, -x0 * ZOOM], [0, ZOOM, -y0 * ZOOM]], np.float32)
    img = cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)
    blur = cv2.GaussianBlur(img, (0, 0), 1.3)
    img = cv2.addWeighted(img, 1.4, blur, -0.4, 0)
    x = img.astype(np.float32) / 255
    x = 0.84 * x + 0.16 * (x * x * (3 - 2 * x))                     # same gentle contrast as the reel
    x[..., 0] *= 1.01; x[..., 2] *= 0.985                            # touch of warmth
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    x *= (1 - 0.08 * (((xx - W / 2) / (W / 2)) ** 2 * 0.6 + ((yy - H / 2) / (H / 2)) ** 2 * 0.4) ** 1.2)[..., None]
    return Image.fromarray(np.clip(x * 255, 0, 255).astype(np.uint8)).convert("RGBA")


def dm(size, wght=700):
    f = ImageFont.truetype(f"{FD}/DMSans-VF.ttf", size)
    f.set_variation_by_axes([min(40, max(9, size / 2.2)), wght])
    return f


def ink(s, f, fill):
    asc, desc = f.getmetrics()
    im = Image.new("RGBA", (int(f.getlength(s)) + 20, asc + desc + 20), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, 10 + asc), s, font=f, fill=fill + (255,), anchor="ls")
    return im, 10 + asc                                               # image and its baseline y


def card():
    f1 = dm(84)
    fi = ImageFont.truetype(f"{FD}/PlayfairDisplay-400i.ttf", 126)
    l1, b1 = ink(LINE1, f1, CHAR)
    a, ba = ink(LINE2A, f1, CHAR)
    b, bb = ink(LINE2B, fi, ORANGE)
    # second line: sans "to Be a " + orange italic "Child?" on one baseline
    base = max(ba, bb)
    w2 = a.width - 10 + b.width
    l2 = Image.new("RGBA", (w2, max(a.height - ba, b.height - bb) + base), (0, 0, 0, 0))
    l2.alpha_composite(a, (0, base - ba)); l2.alpha_composite(b, (a.width - 22, base - bb))
    l1 = l1.crop(l1.getchannel("A").getbbox()); l2 = l2.crop(l2.getchannel("A").getbbox())
    gap, px, py = 22, 62, 50
    cw = max(l1.width, l2.width) + 2 * px
    ch = l1.height + gap + l2.height + 2 * py
    s = 3
    box = Image.new("RGBA", (cw * s, ch * s), (0, 0, 0, 0))
    ImageDraw.Draw(box).rounded_rectangle((0, 0, cw * s - 1, ch * s - 1), 36 * s, fill=WHITE + (250,))
    box = box.resize((cw, ch), Image.LANCZOS)
    box.alpha_composite(l1, ((cw - l1.width) // 2, py))
    box.alpha_composite(l2, ((cw - l2.width) // 2, py + l1.height + gap))
    pad = 60
    out = Image.new("RGBA", (cw + 2 * pad, ch + 2 * pad), (0, 0, 0, 0))
    m = Image.new("L", out.size, 0); m.paste(box.getchannel("A"), (pad, pad + 10))
    m = m.filter(ImageFilter.GaussianBlur(22)).point(lambda v: v * 60 // 255)
    sh = Image.new("RGBA", out.size, (40, 30, 20, 0)); sh.putalpha(m)
    out.alpha_composite(sh); out.alpha_composite(box, (pad, pad))
    return out


def main():
    img = photo()
    c = card()
    img.alpha_composite(c, ((W - c.width) // 2, CARD_CY - c.height // 2))
    out = sys.argv[1]
    img.convert("RGB").save(out, quality=93, subsampling=0)
    # grid preview: the 3:4 centre crop the profile grid shows
    img.convert("RGB").crop((0, 240, 1080, 1680)).resize((540, 720), Image.LANCZOS).save(out.replace(".jpg", "_grid_preview.jpg"), quality=90)
    print("wrote", out)


if __name__ == "__main__":
    main()
