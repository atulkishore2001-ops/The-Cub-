# Builds the registration QR card (brand/osit_register_qr.png) from the supplied WhatsApp QR screenshot: the code is
# redrawn crisply from its 29x29 module grid, the WhatsApp icon is placed back in the centre on a white disc, and the
# card uses the poster's style (white, red frame, "SCAN TO REGISTER" pill).  Usage: qr_card.py <qr screenshot>
import sys
import cv2, numpy as np
from PIL import Image, ImageDraw
import osit_gfx as O

src_path = sys.argv[1]
src = cv2.imread(src_path)
text, pts, straight = cv2.QRCodeDetector().detectAndDecode(src)
mods = straight < 128
N, M = mods.shape[0], 14
qz = 2 * M
size = N * M + 2 * qz
q = Image.new("RGB", (size, size), "white"); d = ImageDraw.Draw(q)
for y in range(N):
    for x in range(N):
        if mods[y, x]:
            d.rectangle((qz + x * M, qz + y * M, qz + (x + 1) * M - 1, qz + (y + 1) * M - 1), fill=(0, 0, 0))
x0, y0, x1, y1 = [int(v) for v in (pts[0][0][0], pts[0][0][1], pts[0][2][0], pts[0][2][1])]
cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
r = int((x1 - x0) * 0.15)
logo = Image.open(src_path).convert("RGB").crop((cx - r, cy - r, cx + r, cy + r))
L = int(size * 0.19); logo = logo.resize((L, L), Image.LANCZOS)
D = int(size * 0.25)


def disc(n):
    m = Image.new("L", (n * 4, n * 4), 0); ImageDraw.Draw(m).ellipse((0, 0, n * 4 - 1, n * 4 - 1), fill=255)
    return m.resize((n, n), Image.LANCZOS)


q.paste(Image.new("RGB", (D, D), "white"), ((size - D) // 2, (size - D) // 2), disc(D))
q.paste(logo, ((size - L) // 2, (size - L) // 2), disc(L))
pad = 22; cw = size + 2 * pad; ch = size + 2 * pad + 18
card = O.rrect(cw, ch, 40, (255, 255, 255, 255), outline=O.RED + (255,), width=7)
card.paste(q, (pad, pad))
lab = O.ink("SCAN TO REGISTER", O.dm(30, 800), (255, 255, 255), tracking=3)
pill = O.rrect(lab.width + 70, 64, 32, O.RED + (255,)); pill.alpha_composite(lab, ((pill.width - lab.width) // 2, (64 - lab.height) // 2))
out = Image.new("RGBA", (cw, ch + 40), (0, 0, 0, 0)); out.alpha_composite(card, (0, 0)); out.alpha_composite(pill, ((cw - pill.width) // 2, ch - 30))
out.save("brand/osit_register_qr.png")
chk = cv2.cvtColor(np.asarray(out.convert("RGB")), cv2.COLOR_RGB2BGR)
print("source decodes to", text)
print("card decodes to  ", cv2.QRCodeDetector().detectAndDecode(chk)[0], "| at 40%:", cv2.QRCodeDetector().detectAndDecode(cv2.resize(chk, None, fx=0.4, fy=0.4))[0])
