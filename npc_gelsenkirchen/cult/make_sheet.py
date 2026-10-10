# Контактный лист концептов культа дыма: python make_sheet.py <папка рендеров>  ->  <папка>/cult_sheet.png
import sys, os
from PIL import Image, ImageDraw, ImageFont

D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "renders")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
f_title = ImageFont.truetype(FONTB, 40)
f_name = ImageFont.truetype(FONTB, 34)
f_txt = ImageFont.truetype(FONT, 19)
f_small = ImageFont.truetype(FONT, 18)

ROWS = [
	("sister", "Сестра дыма", ["≈30 лет, стройная", "длинное белое льняное платье,", "юбка-клёш до щиколоток", "тёмная коса через плечо",
		"верёвочный пояс, босиком", "пепельные мазки: лоб, скулы", "знак: пробитый фильтр"]),
	("brother", "Брат дыма", ["≈45 лет, плотный", "белая туника до колен,", "свободные белые штаны", "короткая борода с проседью",
		"верёвочный пояс, сандалии", "латунное кадило на цепочках", "пепел на лице, фильтр-знак"]),
	("elder", "Старейшина", ["≈65 лет, женщина", "белая роба с капюшоном", "и пелериной, верёвочный пояс", "седые волосы, светлые глаза",
		"серые разводы у глаз и рта", "деревянный посох с обмоткой", "сандалии, фильтр на шнурке"]),
]
W = 1960
PAD = 24
RH = 620
LABEL_W = 420
BG = (24, 25, 27)
FG = (230, 228, 222)
DIM = (160, 160, 158)


def fit_h(im, h):
	return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)


tiles = []
for rid, name, lines in ROWS:
	ims = [fit_h(Image.open(os.path.join(D, "cult_%s_%s.png" % (rid, v))).convert("RGB"), RH) for v in ("front", "34", "face")]
	tiles.append((name, lines, ims))
grp = Image.open(os.path.join(D, "cult_group.png")).convert("RGB")
grp = grp.resize((W - 2 * PAD, round(grp.height * (W - 2 * PAD) / grp.width)), Image.LANCZOS)

H = 110 + len(tiles) * (RH + PAD) + 60 + grp.height + PAD + 50
sheet = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(sheet)
d.text((PAD, 28), "Община Серого Дыхания — сектанты в белом (концепт на утверждение)", font=f_title, fill=FG)
d.text((PAD, 78), "MPFB2 / MakeHuman (CC0) + одежда, смоделированная в скрипте • Cycles, AgX • дымный серый свет города", font=f_small, fill=DIM)
y = 110
for name, lines, ims in tiles:
	d.text((PAD, y + 10), name, font=f_name, fill=FG)
	ty = y + 64
	for ln in lines:
		d.text((PAD, ty), ln, font=f_txt, fill=DIM)
		ty += 31
	d.text((PAD, y + RH - 26), "анфас • 3/4 • лицо", font=f_small, fill=(120, 120, 118))
	x = LABEL_W
	for im in ims:
		sheet.paste(im, (x, y))
		x += im.width + 12
	y += RH + PAD
d.text((PAD, y + 12), "Вместе: Сестра дыма • Старейшина • Брат дыма", font=f_name, fill=FG)
y += 60
sheet.paste(grp, (PAD, y))
out = os.path.join(D, "cult_sheet.png")
sheet.save(out, optimize=True)
print("saved", out, sheet.size)
