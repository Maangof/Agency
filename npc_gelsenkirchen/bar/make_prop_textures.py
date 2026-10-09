# Текстуры мелкого реквизита клуба «Neon» (этикетки, меню, постеры, подставки, граффити).
# Все марки — пародийные (правило проекта). python3 make_prop_textures.py -> props_tex/*.png
import os, random, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "props_tex")
os.makedirs(OUT, exist_ok=True)
FD = "/usr/share/fonts/truetype/dejavu/"
FL = "/usr/share/fonts/truetype/liberation/"
SANS_B, SERIF_B, SERIF, SANS, CONDB = FD + "DejaVuSans-Bold.ttf", FD + "DejaVuSerif-Bold.ttf", FD + "DejaVuSerif.ttf", FD + "DejaVuSans.ttf", FD + "DejaVuSans-Bold.ttf"
MONO_B = FL + "LiberationMono-Bold.ttf"
rnd = random.Random(4)


def font(path, size):
	return ImageFont.truetype(path, size)


def centered(d, y, text, f, fill, W):
	w = d.textlength(text, font=f)
	d.text(((W - w) / 2, y), text, font=f, fill=fill)


def paper_noise(im, amount=14, seed=0):
	r = random.Random(seed)
	px = im.load()
	for _ in range(im.width * im.height // 6):
		x, y = r.randrange(im.width), r.randrange(im.height)
		c = px[x, y]
		k = r.randint(-amount, amount)
		px[x, y] = tuple(max(0, min(255, v + k)) for v in c[:3]) + ((c[3],) if len(c) == 4 else ())
	return im


# --- шрифты из папки fonts/ (Google Fonts, OFL/Apache) --------------------------------
GF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts") + "/"
FRAKTUR, BANGERS, ABRIL, ALFA, RYE = GF + "UnifrakturMaguntia-Book.ttf", GF + "Bangers-Regular.ttf", GF + "AbrilFatface-Regular.ttf", GF + "AlfaSlabOne-Regular.ttf", GF + "Rye-Regular.ttf"
PACIFICO, LOBSTER, CINZEL, OSWALD, BEBAS = GF + "Pacifico-Regular.ttf", GF + "Lobster-Regular.ttf", GF + "Cinzel.ttf", GF + "Oswald.ttf", GF + "BebasNeue-Regular.ttf"
MONOTON, LUCKIEST, PLAYFAIR, VIBES, ANTON, TYPE = GF + "Monoton-Regular.ttf", GF + "LuckiestGuy-Regular.ttf", GF + "PlayfairDisplay.ttf", GF + "GreatVibes-Regular.ttf", GF + "Anton-Regular.ttf", GF + "SpecialElite-Regular.ttf"


def gradient(W, H, c1, c2, vertical=True):
	g = Image.new("RGB", (W, H))
	d = ImageDraw.Draw(g)
	n = H if vertical else W
	for i in range(n):
		t = i / max(1, n - 1)
		c = tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))
		d.line((0, i, W, i) if vertical else (i, 0, i, H), fill=c)
	return g


def aged(im, seed, stains=4, vignette=0.35, fibers=600):
	"""Старая бумага: шум, волокна, пятна, виньетка."""
	r = random.Random(seed)
	im = paper_noise(im.convert("RGB"), 10, seed)
	d = ImageDraw.Draw(im, "RGBA")
	for _ in range(fibers):
		x, y = r.randrange(im.width), r.randrange(im.height)
		d.line((x, y, x + r.randint(-14, 14), y + r.randint(-3, 3)), fill=(0, 0, 0, r.randint(6, 18)), width=1)
	for _ in range(stains):
		x, y, rr = r.randrange(im.width), r.randrange(im.height), r.randint(30, 120)
		d.ellipse((x - rr, y - rr, x + rr, y + rr), outline=(90, 60, 20, 40), width=r.randint(2, 6))
		d.ellipse((x - rr + 8, y - rr + 8, x + rr - 8, y + rr - 8), fill=(120, 90, 40, 14))
	if vignette:
		v = Image.new("L", im.size, 0)
		vd = ImageDraw.Draw(v)
		for k in range(40):
			a = int(255 * vignette * (1 - k / 40) ** 2)
			vd.rectangle((k * im.width // 90, k * im.height // 90, im.width - k * im.width // 90, im.height - k * im.height // 90), outline=a, width=max(1, im.height // 90))
		im = Image.composite(Image.new("RGB", im.size, (20, 12, 5)), im, v.filter(ImageFilter.GaussianBlur(im.height // 20)))
	return im


def fx_text(im, center, text, path, size, fill, stroke=0, stroke_fill=(0, 0, 0), shadow=None, grad=None, spacing=0):
	"""Текст по центру; grad=(c1, c2) — «фольга» вертикальным градиентом; spacing — разрядка (px)."""
	f = font(path, size)
	d0 = ImageDraw.Draw(im)
	if spacing:
		widths = [d0.textlength(ch, font=f) for ch in text]
		total = sum(widths) + spacing * (len(text) - 1)
	else:
		total = d0.textlength(text, font=f)
	bb = f.getbbox(text)
	h = bb[3] - bb[1]
	x0, y0 = center[0] - total / 2, center[1] - h / 2 - bb[1]
	layer = Image.new("L", im.size, 0)
	ld = ImageDraw.Draw(layer)
	strokel = Image.new("L", im.size, 0)
	sd = ImageDraw.Draw(strokel)

	def put(drw, **kw):
		if spacing:
			x = x0
			for ch, w in zip(text, widths):
				drw.text((x, y0), ch, font=f, **kw)
				x += w + spacing
		else:
			drw.text((x0, y0), text, font=f, **kw)
	put(ld, fill=255)
	if stroke:
		put(sd, fill=255, stroke_width=stroke, stroke_fill=255)
	if shadow:
		off, col = shadow
		sh = (strokel if stroke else layer).copy()
		sh = Image.composite(sh, Image.new("L", im.size, 0), sh)
		shifted = Image.new("L", im.size, 0)
		shifted.paste(sh, off)
		im.paste(Image.new("RGB", im.size, col), (0, 0), shifted.filter(ImageFilter.GaussianBlur(2)))
	if stroke:
		im.paste(Image.new("RGB", im.size, stroke_fill), (0, 0), strokel)
	if grad:
		g = gradient(im.width, h + 20, grad[0], grad[1])
		full = Image.new("RGB", im.size, grad[0])
		full.paste(g, (0, int(y0 + bb[1]) - 10))
		im.paste(full, (0, 0), layer)
	else:
		im.paste(Image.new("RGB", im.size, fill), (0, 0), layer)
	return total


def curved_text(im, center, radius, text, path, size, fill, start_deg=-90, bottom=False):
	"""Текст по дуге (для печатей). start_deg — середина надписи; bottom — читается снизу."""
	f = font(path, size)
	d = ImageDraw.Draw(im)
	widths = [d.textlength(ch, font=f) for ch in text]
	total = sum(widths)
	ang = math.radians(start_deg) - (total / radius) / 2 * (-1 if bottom else 1)
	for ch, w in zip(text, widths):
		step = (w / radius) * (-1 if bottom else 1)
		a = ang + step / 2
		x, y = center[0] + radius * math.cos(a), center[1] + radius * math.sin(a)
		t = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
		ImageDraw.Draw(t).text((size // 2, size // 4), ch, font=f, fill=fill)
		rot = -math.degrees(a) - 90 if not bottom else -math.degrees(a) + 90
		t = t.rotate(rot, resample=Image.BICUBIC)
		im.paste(t, (int(x - size), int(y - size)), t)
		ang += step


def seal(im, c, r, col, ring_text, inner, bg=None, inner_font=CINZEL, inner_size=None):
	d = ImageDraw.Draw(im)
	if bg:
		d.ellipse((c[0] - r, c[1] - r, c[0] + r, c[1] + r), fill=bg)
	d.ellipse((c[0] - r, c[1] - r, c[0] + r, c[1] + r), outline=col, width=max(3, r // 18))
	d.ellipse((c[0] - r * 0.72, c[1] - r * 0.72, c[0] + r * 0.72, c[1] + r * 0.72), outline=col, width=max(2, r // 30))
	for k in range(72):
		a = 2 * math.pi * k / 72
		d.line((c[0] + r * 0.93 * math.cos(a), c[1] + r * 0.93 * math.sin(a), c[0] + r * 0.98 * math.cos(a), c[1] + r * 0.98 * math.sin(a)), fill=col, width=2)
	curved_text(im, c, r * 0.8, ring_text, CINZEL, max(12, int(r * 0.15)), col)
	if inner == "pick":
		hammer_pick(d, c, r * 0.42, col)
	elif inner == "tower":
		headframe(d, (c[0], c[1] + r * 0.4), r * 0.85, col)
	else:
		fx_text(im, c, inner, inner_font, inner_size or int(r * 0.45), col)


def hammer_pick(d, c, s, col):
	w = max(4, int(s / 7))
	d.line((c[0] - s, c[1] + s, c[0] + s, c[1] - s), fill=col, width=w)
	d.line((c[0] + s, c[1] + s, c[0] - s, c[1] - s), fill=col, width=w)
	d.rectangle((c[0] + s * 0.55, c[1] - s * 1.15, c[0] + s * 1.15, c[1] - s * 0.65), fill=col)          # молот
	d.arc((c[0] - s * 1.6, c[1] - s * 1.6, c[0] - s * 0.3, c[1] - s * 0.3), 200, 340, fill=col, width=w)  # кирка


def headframe(d, base, s, col):
	"""Шахтный копёр (как на Zollverein) — линиями."""
	x, y = base
	w = max(3, int(s / 30))
	d.line((x - s * 0.35, y, x - s * 0.1, y - s * 0.9), fill=col, width=w)
	d.line((x + s * 0.35, y, x + s * 0.1, y - s * 0.9), fill=col, width=w)
	d.line((x + s * 0.35, y, x + s * 0.7, y - s * 0.55), fill=col, width=w)
	for k in range(4):
		yy = y - s * 0.2 * (k + 1)
		d.line((x - s * 0.35 + k * 0.06 * s, yy, x + s * 0.35 - k * 0.06 * s, yy), fill=col, width=max(2, w // 2))
	for dx in (-0.12, 0.12):
		d.ellipse((x + s * dx - s * 0.1, y - s * 1.0, x + s * dx + s * 0.1, y - s * 0.8), outline=col, width=w)
	d.line((x - s * 0.5, y, x + s * 0.8, y), fill=col, width=w)


def ornate_frame(d, box, col, col2=None, corner=True):
	x0, y0, x1, y1 = box
	d.rectangle(box, outline=col, width=8)
	d.rectangle((x0 + 18, y0 + 18, x1 - 18, y1 - 18), outline=col2 or col, width=3)
	for x in range(int(x0 + 40), int(x1 - 40), 18):
		d.ellipse((x, y0 + 30, x + 5, y0 + 35), fill=col2 or col)
		d.ellipse((x, y1 - 35, x + 5, y1 - 30), fill=col2 or col)
	if corner:
		for cx, cy in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
			d.ellipse((cx - 26, cy - 26, cx + 26, cy + 26), fill=col)
			d.ellipse((cx - 14, cy - 14, cx + 14, cy + 14), fill=col2 or (255, 255, 255))
			for k in range(8):
				a = math.pi * k / 4
				d.ellipse((cx + 34 * math.cos(a) - 5, cy + 34 * math.sin(a) - 5, cx + 34 * math.cos(a) + 5, cy + 34 * math.sin(a) + 5), fill=col)


def ribbon(im, c, w, h, col, text, path, size, tcol):
	d = ImageDraw.Draw(im)
	x, y = c
	tail = h * 0.8
	dark = tuple(int(v * 0.6) for v in col)
	d.polygon([(x - w / 2 - tail, y - h / 2 + 14), (x - w / 2 + 10, y - h / 2 + 14), (x - w / 2 + 10, y + h / 2 + 14), (x - w / 2 - tail, y + h / 2 + 14), (x - w / 2 - tail * 0.6, y + 14)], fill=dark)
	d.polygon([(x + w / 2 + tail, y - h / 2 + 14), (x + w / 2 - 10, y - h / 2 + 14), (x + w / 2 - 10, y + h / 2 + 14), (x + w / 2 + tail, y + h / 2 + 14), (x + w / 2 + tail * 0.6, y + 14)], fill=dark)
	d.rectangle((x - w / 2, y - h / 2, x + w / 2, y + h / 2), fill=col)
	fx_text(im, (x, y), text, path, size, tcol)


def barcode(d, x, y, w, h, col, seed):
	r = random.Random(seed)
	xx = x
	while xx < x + w:
		bw = r.choice((2, 3, 3, 5, 7))
		d.rectangle((xx, y, xx + bw - 1, y + h), fill=col)
		xx += bw + r.choice((2, 3, 4))


def small_print(d, x, y, lines, path, size, col, lh=1.35):
	f = font(path, size)
	for ln in lines:
		d.text((x, y), ln, font=f, fill=col)
		y += int(size * lh)


def juniper(d, x, y, s, leaf, berry, seed):
	r = random.Random(seed)
	for k in range(7):
		a = math.radians(-60 + k * 20)
		ex, ey = x + s * math.cos(a), y - s * math.sin(a) * 0.6 - k * 4
		d.line((x, y, ex, ey), fill=leaf, width=4)
		for j in range(6):
			t = (j + 1) / 7
			px, py = x + (ex - x) * t, y + (ey - y) * t
			d.line((px, py, px + r.randint(-18, 18), py - r.randint(8, 22)), fill=leaf, width=3)
	for _ in range(9):
		lo, hi = sorted((-20, int(s * 0.8)))
		bx, by = x + r.randint(lo, hi), y - r.randint(-10, int(abs(s) * 0.5))
		d.ellipse((bx - 11, by - 11, bx + 11, by + 11), fill=berry)
		d.ellipse((bx - 4, by - 7, bx + 1, by - 2), fill=(200, 210, 240))


def compass(d, c, r, col, col2):
	for k in range(16):
		a = math.pi * k / 8
		rr = r if k % 2 == 0 else r * 0.55
		w = r * (0.16 if k % 2 == 0 else 0.1)
		tip = (c[0] + rr * math.cos(a), c[1] + rr * math.sin(a))
		l = (c[0] + w * math.cos(a + math.pi / 2), c[1] + w * math.sin(a + math.pi / 2))
		rgt = (c[0] + w * math.cos(a - math.pi / 2), c[1] + w * math.sin(a - math.pi / 2))
		d.polygon([tip, l, c], fill=col)
		d.polygon([tip, rgt, c], fill=col2)
	d.ellipse((c[0] - r * 0.12, c[1] - r * 0.12, c[0] + r * 0.12, c[1] + r * 0.12), fill=col)


# --- этикетки бутылок: развёртка по окружности; пропорции = окружность / высота этикетки ---
# (ширина 2048 = полный обхват; лицевая панель — в середине, x 640..1408)
def label_canvas(ratio, bg1, bg2=None):
	W, H = 2048, int(2048 / ratio)
	return (gradient(W, H, bg1, bg2) if bg2 else Image.new("RGB", (W, H), bg1)), W, H


def back_panel(im, H, col, seed, lines):
	d = ImageDraw.Draw(im)
	small_print(d, 1490, int(H * 0.16), lines, TYPE, max(18, H // 22), col)
	barcode(d, 1520, int(H * 0.68), 300, int(H * 0.18), col, seed)
	small_print(d, 1520, int(H * 0.88), ["4 006043 0" + str(seed % 100000).zfill(5)], TYPE, max(14, H // 32), col)
	small_print(d, 140, int(H * 0.2), ["Quarantäne-Abfüllung", "Charge Q-" + str(seed % 9000 + 1000), "Nicht an Graue ausschenken.", "Pfand 0,08 €"], TYPE, max(18, H // 24), col)


# 1. Gelsen Korn — фрактур, кремовая бумага, печать «seit 1923»
im, W, H = label_canvas(2.0, (238, 228, 200), (225, 210, 175))
d = ImageDraw.Draw(im)
ornate_frame(d, (620, 30, 1428, H - 30), (150, 25, 25), (30, 50, 110))
fx_text(im, (1024, int(H * 0.25)), "Gelsen", FRAKTUR, 200, (160, 25, 25), stroke=3, stroke_fill=(40, 20, 10), shadow=((5, 5), (120, 100, 70)))
fx_text(im, (1024, int(H * 0.47)), "KORN", CINZEL, 150, (30, 50, 110), spacing=26)
ribbon(im, (1024, int(H * 0.64)), 520, 74, (30, 50, 110), "DOPPELKORN · 38 % vol", OSWALD, 44, (240, 230, 200))
seal(im, (1024, int(H * 0.84)), 78, (150, 25, 25), "REVIER-BRENNEREI · SEIT 1923 · ", "pick")
back_panel(im, H, (60, 40, 25), 1923, ["Zutaten: Weizen, Roggen,", "Grubenwasser (gefiltert).", "Gebrannt & abgefüllt in", "Gelsenkirchen-Schalke."])
aged(im, 11).save(f"{OUT}/label_korn.png")

# 2. Kohlenpott Kräuter — тёмно-зелёный, золотая фольга, Cinzel + Great Vibes
im, W, H = label_canvas(3.6, (18, 50, 28), (8, 30, 16))
d = ImageDraw.Draw(im)
ornate_frame(d, (600, 22, 1448, H - 22), (200, 160, 70), (120, 95, 40))
fx_text(im, (1024, int(H * 0.3)), "KOHLENPOTT", CINZEL, 96, None, grad=((255, 230, 150), (170, 120, 40)), shadow=((3, 3), (0, 0, 0)), spacing=6)
fx_text(im, (1024, int(H * 0.62)), "Kräuterlikör", VIBES, 96, (230, 200, 120))
small_print(d, 890, int(H * 0.8), ["56 Kräuter · 35 % vol · 0,7 l"], OSWALD, 28, (230, 200, 120))
seal(im, (540, H // 2), 60, (200, 160, 70), "GLÜCK AUF · GLÜCK AUF · ", "pick", bg=(14, 40, 22))
seal(im, (1508, H // 2), 60, (200, 160, 70), "UNTER TAGE · UNTER TAGE · ", "56", bg=(14, 40, 22))
back_panel(im, H, (210, 180, 110), 56, ["56 Kräuter, Wurzeln", "und Kohlenstaub-Aroma."])
aged(im, 12, stains=2, vignette=0.5).save(f"{OUT}/label_kraeuter.png")

# 3. Schicht Rum — Rye, роза ветров, «Stadthafen»
im, W, H = label_canvas(2.7, (35, 22, 14), (20, 12, 8))
d = ImageDraw.Draw(im)
d.rectangle((630, 40, 1418, H - 40), outline=(220, 170, 90), width=6)
compass(d, (1024, int(H * 0.42)), 230, (60, 38, 18), (45, 28, 12))
fx_text(im, (1024, int(H * 0.28)), "SCHICHT", RYE, 140, (235, 205, 140), stroke=4, stroke_fill=(20, 10, 5))
fx_text(im, (1024, int(H * 0.53)), "RUM", ABRIL, 190, (220, 170, 90), stroke=4, stroke_fill=(20, 10, 5), spacing=20)
fx_text(im, (1024, int(H * 0.73)), "Dark · Stadthafen Gelsenkirchen", PLAYFAIR, 46, (235, 205, 140))
fx_text(im, (1024, int(H * 0.86)), "40 % vol · 0,7 l", OSWALD, 40, (220, 170, 90))
back_panel(im, H, (200, 160, 100), 4040, ["Gelagert in Fässern", "am Rhein-Herne-Kanal.", "Nach der Schicht —", "ein Schluck."])
aged(im, 13, stains=5, vignette=0.55).save(f"{OUT}/label_rum.png")

# 4. Revier Gin — светлый, ветка можжевельника, Playfair + Bebas
im, W, H = label_canvas(2.6, (236, 242, 244), (215, 228, 232))
d = ImageDraw.Draw(im)
d.rectangle((640, 36, 1408, H - 36), outline=(20, 80, 100), width=4)
d.rectangle((654, 50, 1394, H - 50), outline=(20, 80, 100), width=1)
juniper(d, 690, int(H * 0.97), 170, (40, 110, 80), (40, 60, 120), 4)
juniper(d, 1358, int(H * 0.97), -170, (40, 110, 80), (40, 60, 120), 5)
fx_text(im, (1024, int(H * 0.22)), "Revier", PLAYFAIR, 120, (20, 80, 100))
fx_text(im, (1024, int(H * 0.47)), "GIN", BEBAS, 260, (15, 45, 60), spacing=30)
fx_text(im, (1024, int(H * 0.68)), "DRY · WACHOLDER & GRUBENGRÜN", OSWALD, 40, (20, 80, 100))
fx_text(im, (1024, int(H * 0.77)), "41 % vol", TYPE, 40, (20, 80, 100))
back_panel(im, H, (20, 70, 90), 4141, ["Botanicals: Wacholder,", "Haldenkräuter, Zitrus."])
aged(im, 14, stains=1, vignette=0.2).save(f"{OUT}/label_gin.png")

# 5. Zollverein Wodka — минимализм, копёр, серебро, красная полоса
im, W, H = label_canvas(2.5, (246, 246, 248))
d = ImageDraw.Draw(im)
d.rectangle((0, int(H * 0.86), W, int(H * 0.9)), fill=(190, 20, 30))
headframe(d, (1024, int(H * 0.52)), 300, (40, 40, 45))
fx_text(im, (1024, int(H * 0.66)), "ZOLLVEREIN", BEBAS, 150, None, grad=((120, 120, 130), (20, 20, 25)), spacing=18)
fx_text(im, (1024, int(H * 0.78)), "WODKA · 40 % VOL · KLAR WIE GRUBENWASSER", OSWALD, 34, (70, 70, 80))
back_panel(im, H, (60, 60, 70), 4000, ["Fünffach destilliert", "über Koks-Aktivkohle."])
aged(im, 15, stains=0, vignette=0.12, fibers=200).save(f"{OUT}/label_vodka.png")

# 6. Halde 12 — пергамент, Abril, медаль
im, W, H = label_canvas(2.5, (215, 180, 115), (190, 150, 85))
d = ImageDraw.Draw(im)
ornate_frame(d, (630, 30, 1418, H - 30), (70, 35, 12), (120, 70, 25))
fx_text(im, (1024, int(H * 0.22)), "HALDE", ABRIL, 150, (60, 28, 8), spacing=10)
fx_text(im, (1024, int(H * 0.46)), "Single Malt", VIBES, 120, (90, 45, 12))
seal(im, (1024, int(H * 0.72)), 105, (70, 35, 12), "12 JAHRE · UNTER TAGE GEREIFT · ", "12", inner_font=ABRIL, inner_size=80)
back_panel(im, H, (60, 30, 10), 1212, ["Gereift 12 Jahre im", "Stollen der Zeche", "auf 900 m Tiefe."])
aged(im, 16, stains=6, vignette=0.5).save(f"{OUT}/label_whisky.png")

# 7. Zeche Pils — Alfa Slab + Lobster, герб с молотом и киркой
im, W, H = label_canvas(3.0, (240, 232, 210))
d = ImageDraw.Draw(im)
d.rounded_rectangle((560, 18, 1488, H - 18), 40, fill=(18, 46, 125), outline=(200, 160, 60), width=8)
d.rounded_rectangle((585, 43, 1463, H - 43), 30, outline=(240, 232, 210), width=3)
fx_text(im, (1024, int(H * 0.3)), "ZECHE", ALFA, 140, (240, 232, 210), shadow=((4, 4), (5, 15, 50)), spacing=8)
fx_text(im, (1024, int(H * 0.6)), "Pils", LOBSTER, 170, (255, 255, 255), shadow=((4, 4), (5, 15, 50)))
ribbon(im, (1024, int(H * 0.86)), 470, 56, (180, 25, 30), "BLAU-WEISS BRÄU · 4,9 %", OSWALD, 36, (255, 255, 255))
seal(im, (700, H // 2), 70, (200, 160, 60), "GEBRAUT IM REVIER · ", "pick", bg=(18, 46, 125))
seal(im, (1348, H // 2), 70, (200, 160, 60), "SEIT 1904 · SEIT 1904 · ", "04", bg=(18, 46, 125), inner_font=ALFA)
back_panel(im, H, (40, 40, 60), 4904, ["Gebraut nach dem", "Reinheitsgebot von 1516."])
aged(im, 17, stains=1, vignette=0.2).save(f"{OUT}/label_beer.png")


# --- подставка под пиво (Bierdeckel), круг 1024 --------------------------------------
im = Image.new("RGB", (1024, 1024), (245, 240, 228))
d = ImageDraw.Draw(im)
d.ellipse((40, 40, 984, 984), fill=(20, 50, 130))
d.ellipse((90, 90, 934, 934), outline=(245, 240, 228), width=10)
centered(d, 300, "NEON", font(SANS_B, 200), (255, 255, 255), 1024)
centered(d, 530, "BLAU · WEISS 04", font(SANS_B, 70), (160, 200, 255), 1024)
centered(d, 640, "Kumpelbar seit 1904", font(SERIF, 52), (245, 240, 228), 1024)
for k in range(5):        # следы от бокала
	r = 300 + k * 6
	d.arc((512 - r, 512 - r + 40, 512 + r, 512 + r + 40), 200 + k * 13, 320 + k * 9, fill=(200, 190, 160), width=3)
paper_noise(im, 12, 3).filter(ImageFilter.GaussianBlur(0.8)).save(f"{OUT}/coaster.png")


# --- меловые доски: над стойкой и у окна выдачи --------------------------------------
def chalkboard(name, title, rows, W=2048, H=1024):
	im = Image.new("RGB", (W, H), (28, 32, 30))
	d = ImageDraw.Draw(im)
	r = random.Random(hash(name) % 999)
	for _ in range(2500):          # разводы мела
		x, y = r.randrange(W), r.randrange(H)
		d.line((x, y, x + r.randint(-60, 60), y + r.randint(-8, 8)), fill=(48, 54, 50), width=r.randint(4, 14))
	d.rectangle((0, 0, W - 1, H - 1), outline=(90, 60, 35), width=40)
	centered(d, 70, title, font(SERIF_B, 110), (245, 245, 235), W)
	fy, fr = 250, font(MONO_B, 64)
	for left, right, col in rows:
		d.text((140, fy), left, font=fr, fill=col)
		rw = d.textlength(right, font=fr)
		d.text((W - 140 - rw, fy), right, font=fr, fill=col)
		dots = "." * 40
		d.text((140 + d.textlength(left, font=fr) + 20, fy), dots[: max(0, int((W - 340 - d.textlength(left, font=fr) - rw) / 38))], font=fr, fill=(120, 125, 120))
		fy += 100
	im = im.filter(ImageFilter.GaussianBlur(1.1))
	paper_noise(im, 18, 5).save(f"{OUT}/{name}.png")


W_ = (245, 245, 235)
Y_ = (250, 220, 120)
P_ = (255, 150, 190)
B_ = (150, 200, 255)
chalkboard("menu_bar", "~ GETRÄNKE ~", [("Zeche Pils 0,3", "2,80", W_), ("Zeche Pils 0,5", "4,20", W_), ("Gelsen Korn 2cl", "2,00", Y_),
	("Kohlenpott Kräuter", "2,50", Y_), ("Revier Gin Tonic", "7,50", B_), ("Herrengedeck", "5,90", P_), ("Fassbrause", "3,00", W_)])
chalkboard("menu_kitchen", "~ IMBISS ~", [("Currywurst", "4,50", W_), ("Pommes rot-weiß", "3,50", W_), ("Currywurst-Pommes", "6,90", Y_),
	("Frikadelle mit Senf", "3,20", W_), ("Schaschlik", "5,40", W_), ("Halve Hahn", "4,00", P_)], H=900)

# --- постеры 1024 × 1448: три в стиле поп-арт и два реалистичных (фото — render_poster_photos.py) ---
PW, PH = 1024, 1448
INK = (15, 12, 10)


def halftone(size, bg, dot, step=22, rmin=2, rmax=9, angle=0.0, center=None, radial=False):
	"""Растровые точки Бен-Дэй: радиус растёт по вертикали или от центра."""
	W, H = size
	im = Image.new("RGB", size, bg)
	d = ImageDraw.Draw(im)
	ca, sa = math.cos(angle), math.sin(angle)
	cx, cy = center or (W / 2, H / 2)
	maxd = math.hypot(W, H) / 2
	for gy in range(-H, 2 * H, step):
		for gx in range(-W, 2 * W, step):
			x = cx + (gx - cx) * ca - (gy - cy) * sa
			y = cy + (gx - cx) * sa + (gy - cy) * ca
			if -step < x < W + step and -step < y < H + step:
				t = (math.hypot(x - cx, y - cy) / maxd) if radial else (y / H)
				r = rmin + (rmax - rmin) * max(0.0, min(1.0, t))
				d.ellipse((x - r, y - r, x + r, y + r), fill=dot)
	return im


def burst(d, c, r_out, r_in, n, fill, outline=INK, width=12, seed=0):
	rr = random.Random(seed)
	pts = []
	for k in range(n * 2):
		a = math.pi * k / n
		r = (r_out * rr.uniform(0.85, 1.1)) if k % 2 == 0 else r_in
		pts.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))
	d.polygon(pts, fill=fill, outline=outline)
	d.line(pts + [pts[0]], fill=outline, width=width, joint="curve")


def comic_text(im, c, text, path, size, fill, stroke=10, shadow=12, angle=0):
	"""Комиксный текст: толстый контур и смещённая тень; можно наклонить."""
	layer = Image.new("RGBA", (PW * 2, PH), (0, 0, 0, 0))
	cc = (PW, PH // 2)
	f = font(path, size)
	ld = ImageDraw.Draw(layer)
	w = ld.textlength(text, font=f)
	bb = f.getbbox(text)
	x, y = cc[0] - w / 2, cc[1] - (bb[3] + bb[1]) / 2
	ld.text((x + shadow, y + shadow), text, font=f, fill=INK + (255,), stroke_width=stroke, stroke_fill=INK + (255,))
	ld.text((x, y), text, font=f, fill=fill + (255,), stroke_width=stroke, stroke_fill=INK + (255,))
	if angle:
		layer = layer.rotate(angle, resample=Image.BICUBIC, center=cc)
	im.paste(layer, (int(c[0] - cc[0]), int(c[1] - cc[1])), layer)


def panel_border(im, inset=26, width=14):
	d = ImageDraw.Draw(im)
	d.rectangle((inset, inset, PW - inset, PH - inset), outline=INK, width=width)


def bubble(d, box, tail, fill=(255, 255, 255)):
	d.polygon(tail, fill=fill, outline=INK)
	d.line(tail[:2], fill=INK, width=10)
	d.line(tail[1:], fill=INK, width=10)
	d.ellipse(box, fill=fill, outline=INK, width=10)
	d.polygon([(tail[0][0] + 12, tail[0][1] - 6), tail[1], (tail[2][0] - 12, tail[2][1] - 6)], fill=fill)


def wear(im, seed):
	"""Лёгкий износ печати: сгибы, царапины, скотч."""
	r = random.Random(seed)
	d = ImageDraw.Draw(im, "RGBA")
	d.line((0, PH // 2 + r.randint(-6, 6), PW, PH // 2 + r.randint(-6, 6)), fill=(255, 255, 255, 40), width=3)
	d.line((PW // 2 + r.randint(-6, 6), 0, PW // 2 + r.randint(-6, 6), PH), fill=(255, 255, 255, 30), width=2)
	for _ in range(80):
		x, y = r.randrange(PW), r.randrange(PH)
		d.line((x, y, x + r.randint(-30, 30), y + r.randint(-4, 4)), fill=(255, 255, 255, r.randint(15, 45)), width=1)
	for (x, y, a) in [(30, 10, -8), (PW - 170, 14, 6), (40, PH - 60, 5), (PW - 160, PH - 56, -7)]:
		t = Image.new("RGBA", (150, 50), (235, 230, 205, 170))
		t = t.rotate(a, expand=True)
		im.paste(t, (x, y), t)
	return paper_noise(im, 10, seed).filter(ImageFilter.GaussianBlur(0.6))


# 1. Дерби — поп-арт: точки, «взрыв» TOOOR!, синие полосы
im = halftone((PW, PH), (250, 215, 30), (230, 60, 40), 26, 2, 11, math.radians(18))
d = ImageDraw.Draw(im)
d.polygon([(0, 0), (PW, 0), (PW, 300), (0, 380)], fill=(20, 50, 140), outline=INK)
d.line([(0, 380), (PW, 300)], fill=INK, width=14)
comic_text(im, (PW // 2, 150), "BLAU-WEISS 04", BANGERS, 130, (255, 255, 255), 8, 10, 3)
burst(d, (PW // 2, 720), 430, 270, 16, (255, 255, 255), seed=3)
burst(d, (PW // 2, 720), 330, 220, 14, (60, 140, 255), seed=4)
comic_text(im, (PW // 2, 680), "TOOOR!", BANGERS, 230, (255, 240, 60), 12, 14, -8)
comic_text(im, (PW // 2, 860), "DAS DERBY", LUCKIEST, 80, (255, 255, 255), 8, 8, -4)
d.rectangle((70, 1130, PW - 70, 1330), fill=(255, 255, 255), outline=INK, width=12)
fx_text(im, (PW // 2, 1185), "SAMSTAG · 15:30 · GROSSBILDLEINWAND", OSWALD, 46, INK)
fx_text(im, (PW // 2, 1260), "Jedes Tor: eine Runde Gelsen Korn!", LOBSTER, 50, (200, 30, 30))
panel_border(im)
wear(im, 21).save(f"{OUT}/poster_derby.png")

# 2. «Nur mit Maske tanzen!» — поп-арт: противогаз, пузырь реплики
im = halftone((PW, PH), (90, 200, 230), (30, 110, 190), 24, 1, 10, math.radians(-20), (PW / 2, PH * 0.55), True)
d = ImageDraw.Draw(im)
cx, cy = PW // 2, 900
d.ellipse((cx - 330, cy - 260, cx + 330, cy + 300), fill=(255, 205, 170), outline=INK, width=14)            # лицо
d.pieslice((cx - 360, cy - 330, cx + 360, cy + 250), 180, 360, fill=(250, 60, 140), outline=INK, width=14)  # волосы
for k in range(7):
	d.arc((cx - 360 + k * 40, cy - 330 + k * 12, cx + 360 - k * 40, cy + 250), 200, 340, fill=(180, 20, 90), width=6)
d.rounded_rectangle((cx - 250, cy - 120, cx + 250, cy + 230), 140, fill=(70, 80, 60), outline=INK, width=14)  # маска
for ex in (-120, 120):
	d.ellipse((cx + ex - 90, cy - 90, cx + ex + 90, cy + 70), fill=(40, 230, 220), outline=INK, width=14)
	d.ellipse((cx + ex - 60, cy - 70, cx + ex - 20, cy - 35), fill=(255, 255, 255))
d.polygon([(cx - 90, cy + 120), (cx + 90, cy + 120), (cx + 120, cy + 330), (cx - 120, cy + 330)], fill=(140, 145, 150), outline=INK)
d.line([(cx - 90, cy + 120), (cx - 120, cy + 330), (cx + 120, cy + 330), (cx + 90, cy + 120)], fill=INK, width=12)
for k in range(5):
	yy = cy + 160 + k * 34
	d.line((cx - 95 - k * 5, yy, cx + 95 + k * 5, yy), fill=INK, width=6)
d.line((cx - 250, cy + 40, cx - 330, cy - 40), fill=INK, width=18)
d.line((cx + 250, cy + 40, cx + 330, cy - 40), fill=INK, width=18)
bubble(d, (60, 70, PW - 60, 470), [(cx - 40, 440), (cx + 70, 610), (cx + 80, 440)])
comic_text(im, (PW // 2, 190), "NUR MIT MASKE", BANGERS, 120, (230, 30, 40), 6, 6, -2)
comic_text(im, (PW // 2, 330), "TANZEN!", BANGERS, 170, (20, 20, 20), 4, 6, -2)
d.rectangle((40, PH - 190, PW - 40, PH - 60), fill=(255, 235, 60), outline=INK, width=10)
fx_text(im, (PW // 2, PH - 145), "QUARANTÄNE-VERORDNUNG § 04", OSWALD, 44, INK)
fx_text(im, (PW // 2, PH - 95), "GelsenOS wünscht viel Spaß", TYPE, 34, INK)
panel_border(im)
wear(im, 22).save(f"{OUT}/poster_maske.png")

# 3. «Schicht im Schacht» — поп-арт: часы 03:00, неоновый шрифт, точки
im = halftone((PW, PH), (30, 10, 50), (255, 40, 150), 30, 1, 8, math.radians(45), (PW / 2, 760), True)
d = ImageDraw.Draw(im)
burst(d, (PW // 2, 300), 360, 240, 18, (255, 230, 40), seed=8)
comic_text(im, (PW // 2, 250), "SCHICHT", BANGERS, 170, (255, 60, 160), 10, 10, -6)
comic_text(im, (PW // 2, 390), "IM SCHACHT!", BANGERS, 120, (40, 200, 255), 10, 10, -6)
c, r = (PW // 2, 800), 250
d.ellipse((c[0] - r - 14, c[1] - r - 14, c[0] + r + 14, c[1] + r + 14), fill=INK)
d.ellipse((c[0] - r, c[1] - r, c[0] + r, c[1] + r), fill=(255, 250, 235))
for k in range(12):
	a = math.pi * k / 6 - math.pi / 2
	fx_text(im, (c[0] + r * 0.78 * math.cos(a), c[1] + r * 0.78 * math.sin(a)), str(12 if k == 0 else k), BANGERS, 54, INK)
d.line((c[0], c[1], c[0], c[1] - r * 0.7), fill=INK, width=18)
d.line((c[0], c[1], c[0] + r * 0.5, c[1]), fill=(230, 30, 60), width=22)
d.ellipse((c[0] - 22, c[1] - 22, c[0] + 22, c[1] + 22), fill=INK)
fx_text(im, (PW // 2, 1150), "03:00", MONOTON, 150, (255, 80, 200))
d.rectangle((60, 1250, PW - 60, 1380), fill=(255, 255, 255), outline=INK, width=10)
fx_text(im, (PW // 2, 1295), "LETZTE RUNDE · LETZTE BAHN 301", OSWALD, 44, INK)
fx_text(im, (PW // 2, 1345), "Wer den Nebel sieht, geht heim.", PLAYFAIR, 34, (90, 20, 80))
panel_border(im)
wear(im, 23).save(f"{OUT}/poster_lastcall.png")


# 4–5. Реалистичные: фото + вёрстка
def photo_poster(name, photo, build, seed):
	path = os.path.join(OUT, photo)
	if not os.path.exists(path):
		print("нет фото", photo, "— запусти render_poster_photos.py")
		return
	ph = Image.open(path).convert("RGB").resize((PW, PH), Image.LANCZOS)
	build(ph)
	wear(ph, seed).save(f"{OUT}/{name}.png")


def _rock(im):
	d = ImageDraw.Draw(im, "RGBA")
	g = gradient(PW, 520, (0, 0, 0), (0, 0, 0))
	mask = gradient(PW, 520, (220, 220, 220), (0, 0, 0)).convert("L")
	im.paste(g, (0, 0), mask)
	mask2 = gradient(PW, 560, (0, 0, 0), (240, 240, 240)).convert("L")
	im.paste(Image.new("RGB", (PW, 560), (0, 0, 0)), (0, PH - 560), mask2)
	fx_text(im, (PW // 2, 120), "KUMPEL", ANTON, 190, (255, 255, 255), spacing=14)
	fx_text(im, (PW // 2, 290), "ROCK NIGHT", ANTON, 120, (255, 60, 70), spacing=10)
	fx_text(im, (PW // 2, 1040), "LIVE IM NEON", OSWALD, 70, (255, 255, 255), spacing=8)
	fx_text(im, (PW // 2, 1120), "FREITAG · 22 UHR · EINLASS 21 UHR", OSWALD, 42, (220, 220, 230))
	d.line((140, 1175, PW - 140, 1175), fill=(255, 60, 70, 255), width=4)
	fx_text(im, (PW // 2, 1235), "DIE STEIGER · HALDE 9 · GRUBENGAS", BEBAS, 64, (255, 255, 255), spacing=4)
	fx_text(im, (PW // 2, 1320), "Eintritt nur mit gültigem Passierschein · Schleuse beachten", TYPE, 28, (190, 190, 200))


def _pils(im):
	d = ImageDraw.Draw(im, "RGBA")
	mask = gradient(PW, 460, (230, 230, 230), (0, 0, 0)).convert("L")
	im.paste(Image.new("RGB", (PW, 460), (5, 10, 30)), (0, 0), mask)
	mask2 = gradient(PW, 520, (0, 0, 0), (245, 245, 245)).convert("L")
	im.paste(Image.new("RGB", (PW, 520), (5, 10, 30)), (0, PH - 520), mask2)
	fx_text(im, (PW // 2, 130), "ZECHE PILS", ALFA, 120, None, grad=((255, 235, 170), (200, 150, 60)), shadow=((4, 4), (0, 0, 0)), spacing=6)
	fx_text(im, (PW // 2, 270), "Das Bier nach der Schicht.", LOBSTER, 72, (255, 255, 255), shadow=((3, 3), (0, 0, 0)))
	fx_text(im, (PW // 2, 1190), "Frisch gezapft im NEON", OSWALD, 56, (255, 255, 255), spacing=4)
	fx_text(im, (PW // 2, 1265), "0,3 l · 2,80 €   |   0,5 l · 4,20 €", BEBAS, 62, (255, 215, 120), spacing=3)
	fx_text(im, (PW // 2, 1345), "Blau-Weiß Bräu · Gelsenkirchen · gebraut nach dem Reinheitsgebot", TYPE, 24, (180, 190, 210))


photo_poster("poster_rocknight", "photo_stage.png", _rock, 24)
photo_poster("poster_pils", "photo_beer.png", _pils, 25)


# --- граффити и наклейки для WC (прозрачный фон) ---------------------------------------
im = Image.new("RGBA", (2048, 1024), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
tags = [("S04", (60, 120, 255), SANS_B, 220, (80, 80), -8), ("Kalle war hier", (230, 230, 230), SERIF_B, 90, (900, 120), 4),
	("NEBEL = LÜGE", (255, 60, 60), SANS_B, 120, (300, 520), -3), ("Glück auf!", (255, 220, 60), SERIF_B, 110, (1150, 560), 6),
	("Wer war Yıldız?", (120, 255, 160), SANS_B, 70, (1250, 330), -5)]
for k in range(14):   # наклейки
	x, y = rnd.choice([rnd.randrange(30, 250), rnd.randrange(1750, 1950)]), rnd.randrange(30, 960)
	col = rnd.choice([(255, 255, 255), (255, 220, 0), (20, 60, 160), (220, 30, 60)])
	d.rectangle((x, y, x + rnd.randint(60, 140), y + rnd.randint(40, 90)), fill=col + (220,))
for text, col, path, size, pos, ang in tags:
	t = Image.new("RGBA", (1400, 400), (0, 0, 0, 0))
	ImageDraw.Draw(t).text((20, 20), text, font=font(path, size), fill=col + (230,))
	t = t.rotate(ang, expand=True, resample=Image.BICUBIC)
	im.alpha_composite(t, pos)
im.save(f"{OUT}/graffiti_wc.png")

# --- знак «Notausgang» (пиктограмма) ----------------------------------------------------
im = Image.new("RGB", (1024, 512), (0, 140, 70))
d = ImageDraw.Draw(im)
d.rectangle((560, 70, 960, 442), outline=(255, 255, 255), width=24)
d.rectangle((600, 110, 760, 402), fill=(255, 255, 255))
d.ellipse((240, 60, 330, 150), fill=(255, 255, 255))
d.line((290, 160, 250, 320), fill=(255, 255, 255), width=48)
d.line((250, 320, 330, 440), fill=(255, 255, 255), width=40)
d.line((250, 320, 160, 430), fill=(255, 255, 255), width=40)
d.line((270, 220, 380, 280), fill=(255, 255, 255), width=34)
d.line((270, 220, 170, 260), fill=(255, 255, 255), width=34)
d.polygon([(400, 236), (500, 236), (500, 196), (560, 256), (500, 316), (500, 276), (400, 276)], fill=(255, 255, 255))
im.save(f"{OUT}/sign_exit.png")
print("ok", sorted(os.listdir(OUT)))
