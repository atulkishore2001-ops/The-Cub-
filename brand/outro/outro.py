# The Cub standard closing frame (logo reveal + tagline), exactly as used at the end of the Anjali
# learning-disabilities reel. Use it to end every reel.
#
#   import outro
#   img = outro.frame(t, base)   # t = seconds since the last spoken word ended; base = that video frame (PIL RGB) or None
#
# Timeline (t = 0 at the end of the last word; the reel should run OUTRO_LEN seconds past it):
#   -0.10 .. 0.90  picture cross-fades to cream (ease in-out); captions hide from +0.10
#    0.55 .. 1.65  logo fades in (ease) while settling from 94% to 100% scale
#    1.40 .. 2.55  tagline "Every Child Deserves To Be Seen" (Playfair Display Italic) is revealed by a soft
#                  left-to-right ink wipe while rising 12 px
#    2.10 .. 2.70  short orange rule (110 x 6 px) draws out under the tagline
#    2.70 .. 4.20  hold
# Sound: a soft chime at +0.60 (about -22 dB under the voice); the music resolves on a final chord at +0.55 and
# fades out over the last 2.6 s, so there is no hard stop.
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
LOGO = os.environ.get("CUB_LOGO", os.path.join(HERE, "..", "logo", "logo_full.png"))
FONT = os.environ.get("CUB_PLAYFAIR_ITALIC", "/tmp/claude-0/fonts/PlayfairDisplay-Italic-VF.ttf")   # google/fonts ofl/playfairdisplay

W, H = 1080, 1920
ORANGE, CHAR, CREAM = (240, 133, 62), (43, 43, 43), (253, 246, 238)
TAGLINE = "Every Child Deserves To Be Seen"
OUTRO_LEN = 4.20                      # seconds of reel after the last word (the Anjali reel used 4.3 from timeline end)
T_CREAM0, T_CREAM1 = -0.10, 0.90
T_LOGO = T_CREAM0 + 0.65
T_TAG = T_LOGO + 0.85
LOGO_W, LOGO_Y = 420, 820             # logo width and centre y
TAG_SIZE, TAG_Y = 60, 1130            # tagline size and centre y
RULE_Y, RULE_W = 1212, 110


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease_out(p):
    return 1 - (1 - p) ** 3


def ease_io(p):
    return 3 * p * p - 2 * p * p * p


def _with_alpha(im, k):
    if k >= 0.999:
        return im
    im = im.copy()
    im.putalpha(im.getchannel("A").point(lambda v: int(v * k)))
    return im


def _tagline():
    f = ImageFont.truetype(FONT, TAG_SIZE)
    f.set_variation_by_axes([500])
    asc, desc = f.getmetrics()
    w = int(f.getlength(TAGLINE)) + 24
    im = Image.new("RGBA", (w, asc + desc + 20), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((12, 10 + asc), TAGLINE, font=f, fill=CHAR + (255,), anchor="ls")
    bb = im.getchannel("A").getbbox()
    top, bot = 10 + asc - int(TAG_SIZE * 0.80), 10 + asc + int(TAG_SIZE * 0.30)
    return im.crop((bb[0] - 2, max(0, min(top, bb[1] - 2)), bb[2] + 2, max(bot, bb[3] + 2)))


_logo = Image.open(LOGO).convert("RGBA")
_logo = _logo.resize((LOGO_W, int(LOGO_W * _logo.height / _logo.width)), Image.LANCZOS)
_tag = _tagline()


def _wipe(im, p, feather=140):
    if p >= 1:
        return im
    m = Image.new("L", im.size, 0)
    x = int((im.width + feather) * p)
    grad = Image.linear_gradient("L").rotate(90).resize((feather, im.height))
    m.paste(255, (0, 0, max(0, x - feather), im.height))
    m.paste(grad, (x - feather, 0))
    out = im.copy()
    a = np.asarray(im.getchannel("A")).astype(np.uint16) * np.asarray(m) // 255
    out.putalpha(Image.fromarray(a.astype(np.uint8)))
    return out


def _paste(frame, im, cx, cy):
    frame.alpha_composite(im, (int(round(cx - im.width / 2)), int(round(cy - im.height / 2))))


def cream_alpha(t):
    return ease_io(clamp((t - T_CREAM0) / (T_CREAM1 - T_CREAM0)))


def frame(t, base=None):
    """Closing-frame image at time t (seconds since the last word ended). base: the reel's video frame at that time."""
    k = cream_alpha(t)
    cream = Image.new("RGB", (W, H), CREAM)
    img = cream if base is None or k >= 0.999 else Image.blend(base.convert("RGB"), cream, k)
    out = img.convert("RGBA")
    p = clamp((t - T_LOGO) / 1.1)
    if p > 0:
        s = 0.94 + 0.06 * ease_out(p)
        lg = _logo.resize((int(_logo.width * s), int(_logo.height * s)), Image.LANCZOS) if s < 0.999 else _logo
        _paste(out, _with_alpha(lg, ease_io(clamp(p * 1.3))), W / 2, LOGO_Y)
    p = clamp((t - T_TAG) / 1.15)
    if p > 0:
        dy = 12 * (1 - ease_out(clamp((t - T_TAG) / 1.0)))
        _paste(out, _with_alpha(_wipe(_tag, ease_io(p)), clamp(p * 2.5)), W / 2, TAG_Y + dy)
    p = ease_io(clamp((t - T_TAG - 0.7) / 0.6))
    if t >= T_TAG + 0.7:
        w = max(2, int(RULE_W * p))
        r = Image.new("RGBA", (w * 3, 18), (0, 0, 0, 0))
        ImageDraw.Draw(r).rounded_rectangle((0, 0, w * 3 - 1, 17), 9, fill=ORANGE + (255,))
        _paste(out, r.resize((w, 6), Image.LANCZOS), W / 2, RULE_Y)
    return out.convert("RGB")


if __name__ == "__main__":                  # render the reference clip: python3 outro.py out.mp4 [base.png]
    import sys, subprocess
    base = Image.open(sys.argv[2]).convert("RGB") if len(sys.argv) > 2 else None
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30",
                            "-i", "-", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", sys.argv[1]], stdin=subprocess.PIPE)
    n0, n1 = int(-0.5 * 30), int(OUTRO_LEN * 30)
    for n in range(n0, n1):
        enc.stdin.write(frame(n / 30, base).tobytes())
    enc.stdin.close(); enc.wait()
    frame(OUTRO_LEN, base).save(sys.argv[1].rsplit(".", 1)[0] + "_final.png")
