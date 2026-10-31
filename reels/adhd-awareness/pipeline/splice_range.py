# Re-render only frames [a, b) of an existing render and copy the rest. Usage: splice_range.py in.mp4 out.mp4 a b
import sys, subprocess
import render_adhd as R
src, out, a, b = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
W, H = 1080, 1920
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30", "-i", "-",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
for n in range(R.TOTAL):
    buf = dec.stdout.read(W * H * 3)
    enc.stdin.write(R.render_frame(n).tobytes() if a <= n < b else buf)
enc.stdin.close(); enc.wait()
print("done")
