# One-page PDF of the reel's spoken script.
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle

F = "/tmp/claude-0/fonts"
for name in ("Medium", "SemiBold", "Bold", "Black"):
    pdfmetrics.registerFont(TTFont(f"Poppins-{name}", f"{F}/Poppins-{name}.ttf"))

INK, GREY, ACCENT = HexColor("#181B34"), HexColor("#8A8FA3"), HexColor("#E0A800")
LINES = [
    ("0:00", "The school bus is five minutes away."),
    ("0:02", "And you've told your child to put on their shoes at least three times now."),
    ("0:05", "They're still looking for their socks."),
    ("0:06", "Does this sound familiar?"),
    ("0:07", "Hi, I'm Saisha and I'm a developmental psychologist."),
    ("0:10", "Your child might know exactly what they need to do, but knowing and doing are two completely different things."),
    ("0:16", "So the skills that help us plan, follow instructions, get started and avoid distractions, they're called executive skills."),
    ("0:24", "You can think of them as the brain's management system."),
    ("0:26", "These skills don't come fully developed. They grow gradually through childhood and adolescence."),
    ("0:31", "So for some kids, especially those with ADHD or autism, it could be more difficult to use these skills consistently."),
    ("0:37", "So what might look like ignoring or not listening to you might actually be a child who's struggling to organize themselves."),
    ("0:43", "So what can you do?"),
    ("0:44", "Instead of repeating the same instructions, we can try to break down the task."),
    ("0:48", "Give a single instruction at a time, or have a visual schedule that they can follow."),
    ("0:52", "Keep the morning routine predictable."),
    ("0:54", "Your child will begin to do things independently, without you having to remind them."),
]

title = ParagraphStyle("t", fontName="Poppins-Black", fontSize=22, leading=27, textColor=INK)
sub = ParagraphStyle("s", fontName="Poppins-Medium", fontSize=10, leading=14, textColor=GREY)
body = ParagraphStyle("b", fontName="Poppins-Medium", fontSize=11.5, leading=17, textColor=INK)
ts = ParagraphStyle("ts", fontName="Poppins-SemiBold", fontSize=10, leading=17, textColor=ACCENT)
foot = ParagraphStyle("f", fontName="Poppins-Medium", fontSize=9, leading=12, textColor=GREY)

words = sum(len(t.split()) for _, t in LINES)
doc = SimpleDocTemplate(sys.argv[1], pagesize=A4, leftMargin=22 * mm, rightMargin=22 * mm, topMargin=22 * mm,
                        bottomMargin=18 * mm, title="Reel Script: Executive Skills", author="The Cub")
rows = [[Paragraph(a, ts), Paragraph(b, body)] for a, b in LINES]
tbl = Table(rows, colWidths=[16 * mm, None])
tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                         ("RIGHTPADDING", (0, 0), (0, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                         ("TOPPADDING", (0, 0), (-1, -1), 0)]))
story = [Paragraph("Reel Script: Executive Skills", title), Spacer(1, 3),
         Paragraph("THE CUB  ·  Saisha, Developmental Psychologist", sub), Spacer(1, 16), tbl, Spacer(1, 10),
         Paragraph(f"{words} words  ·  0:59 reel", foot)]
doc.build(story)
print(words)
