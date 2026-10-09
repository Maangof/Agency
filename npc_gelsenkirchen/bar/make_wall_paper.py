# Расклейка на стенах клуба «Neon»: листовки, объявления, рваные слои афиш, картон, фанера.
# Тексты связаны с лором (дефицит электричества, «Оставшиеся», культ дыма, пропавшие питомцы, бандиты).
# python3 make_wall_paper.py -> props_tex/flyer_*.png, torn_layers.png, cardboard.png, plywood.png, tape.png
import os, random, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "props_tex")
GF = os.path.join(HERE, "fonts") + "/"
FD = "/usr/share/fonts/truetype/dejavu/"
F = {"bangers": GF + "Bangers-Regular.ttf", "anton": GF + "Anton-Regular.ttf", "oswald": GF + "Oswald.ttf", "type": GF + "SpecialElite-Regular.ttf",
	"fraktur": GF + "UnifrakturMaguntia-Book.ttf", "lobster": GF + "Lobster-Regular.ttf", "bebas": GF + "BebasNeue-Regular.ttf",
	"cinzel": GF + "Cinzel.ttf", "playfair": GF + "PlayfairDisplay.ttf", "sans": FD + "DejaVuSans.ttf", "sansb": FD + "DejaVuSans-Bold.ttf",
	"monoton": GF + "Monoton-Regular.ttf", "rye": GF + "Rye-Regular.ttf"}
rnd = random.Random(42)


def fnt(k, s):
	return ImageFont.truetype(F[k], s)


def center_text(d, W, y, text, k, s, col):
	f = fnt(k, s)
	for ln in text.split("\n"):
		w = d.textlength(ln, font=f)
		d.text(((W - w) / 2, y), ln, font=f, fill=col)
		y += int(s * 1.18)
	return y


def torn_alpha(W, H, seed, depth=18, edges="tblr"):
	"""Маска с рваными краями."""
	r = random.Random(seed)
	m = Image.new("L", (W, H), 0)
	pts = []
	step = 14
	for x in range(0, W + 1, step):
		pts.append((x, (r.randint(0, depth) if "t" in edges else 0)))
	for y in range(0, H + 1, step):
		pts.append((W - (r.randint(0, depth) if "r" in edges else 0), y))
	for x in range(W, -1, -step):
		pts.append((x, H - (r.randint(0, depth) if "b" in edges else 0)))
	for y in range(H, -1, -step):
		pts.append(((r.randint(0, depth) if "l" in edges else 0), y))
	ImageDraw.Draw(m).polygon(pts, fill=255)
	return m


def age(im, seed, amount=1.0):
	r = random.Random(seed)
	im = im.convert("RGB")
	d = ImageDraw.Draw(im, "RGBA")
	W, H = im.size
	for _ in range(int(3 * amount)):                         # подтёки воды
		x = r.randrange(W)
		d.rectangle((x, 0, x + r.randint(10, 40), r.randint(H // 3, H)), fill=(110, 90, 50, r.randint(15, 35)))
	for _ in range(int(900 * amount)):                       # грязь, точки
		x, y = r.randrange(W), r.randrange(H)
		d.point((x, y), fill=(40, 30, 20, r.randint(30, 90)))
	for _ in range(int(40 * amount)):                        # царапины
		x, y = r.randrange(W), r.randrange(H)
		d.line((x, y, x + r.randint(-60, 60), y + r.randint(-10, 10)), fill=(255, 255, 255, r.randint(20, 60)), width=1)
	y = r.randint(H // 3, H * 2 // 3)                        # сгиб
	d.line((0, y, W, y + r.randint(-8, 8)), fill=(0, 0, 0, 30), width=2)
	# пожелтение к краям
	g = Image.new("RGB", im.size, (150, 120, 60))
	mask = Image.new("L", im.size, 0)
	md = ImageDraw.Draw(mask)
	for k in range(20):
		md.rectangle((k * W // 60, k * H // 60, W - k * W // 60, H - k * H // 60), outline=int(70 * (1 - k / 20) * amount), width=max(1, W // 60))
	im = Image.composite(g, im, mask.filter(ImageFilter.GaussianBlur(W // 25)))
	return im.filter(ImageFilter.GaussianBlur(0.5))


def flyer(name, size, bg, draw_fn, seed, torn=True):
	W, H = size
	im = Image.new("RGB", (W, H), bg)
	d = ImageDraw.Draw(im)
	draw_fn(im, d, W, H)
	im = age(im, seed)
	a = torn_alpha(W, H, seed, 16 if torn else 2)
	im = im.convert("RGBA")
	im.putalpha(a)
	im.save(f"{OUT}/{name}.png")


INK = (20, 18, 16)


def f_power(im, d, W, H):          # официальное: отключения электричества
	d.rectangle((0, 0, W, 120), fill=(30, 60, 120))
	center_text(d, W, 30, "GelsenOS · BEKANNTMACHUNG", "oswald", 40, (255, 255, 255))
	y = center_text(d, W, 170, "STROMRATIONIERUNG", "anton", 70, (180, 20, 20))
	y = center_text(d, W, y + 20, "Bezirk Altstadt / Neustadt", "type", 32, INK)
	rows = [("Mo–Fr", "18:00 – 22:00"), ("Sa", "16:00 – 23:00"), ("So", "kein Strom"), ("Generatoren", "nur Schleusen & Felder")]
	y += 30
	for a, b in rows:
		d.text((70, y), a, font=fnt("type", 34), fill=INK)
		d.text((W - 70 - d.textlength(b, font=fnt("type", 34)), y), b, font=fnt("type", 34), fill=INK)
		d.line((70, y + 46, W - 70, y + 46), fill=(120, 120, 120), width=1)
		y += 62
	center_text(d, W, H - 190, "Wer Felder sabotiert, wird\nohne Passierschein ausgewiesen.", "type", 28, (60, 60, 60))
	d.rectangle((W - 220, H - 120, W - 60, H - 40), outline=(30, 60, 120), width=4)
	d.text((W - 205, H - 100), "Az. Q-04/17", font=fnt("type", 26), fill=(30, 60, 120))


def f_cat(im, d, W, H):            # пропала кошка (домоседы)
	center_text(d, W, 40, "VERMISST!", "anton", 110, (200, 20, 20))
	d.rectangle((90, 210, W - 90, 640), fill=(200, 200, 200), outline=INK, width=4)
	cx, cy = W // 2, 440                                   # кошка (силуэт)
	d.ellipse((cx - 120, cy - 40, cx + 120, cy + 170), fill=(60, 50, 45))
	d.ellipse((cx - 80, cy - 170, cx + 80, cy - 10), fill=(60, 50, 45))
	d.polygon([(cx - 80, cy - 120), (cx - 60, cy - 220), (cx - 20, cy - 150)], fill=(60, 50, 45))
	d.polygon([(cx + 80, cy - 120), (cx + 60, cy - 220), (cx + 20, cy - 150)], fill=(60, 50, 45))
	d.ellipse((cx - 45, cy - 110, cx - 20, cy - 85), fill=(220, 200, 60))
	d.ellipse((cx + 20, cy - 110, cx + 45, cy - 85), fill=(220, 200, 60))
	y = center_text(d, W, 670, "Katze MIMI, 9 Jahre", "oswald", 54, INK)
	y = center_text(d, W, y + 10, "Seit dem Nebel vom 3. nicht\nnach Hause gekommen.\nBitte bei Familie Kowalczyk,\nWildenbruchstr., klingeln (Schleuse 2)", "type", 32, INK)
	for k in range(8):                                      # отрывные полоски
		x = 40 + k * (W - 80) // 8
		d.line((x, H - 200, x, H), fill=(120, 120, 120), width=2)
		t = Image.new("RGBA", (200, 60), (0, 0, 0, 0))
		ImageDraw.Draw(t).text((0, 0), "Schl. 2 · Mimi", font=fnt("type", 26), fill=INK)
		t = t.rotate(90, expand=True)
		im.paste(t, (x + 12, H - 195), t)


def f_cult(im, d, W, H):           # проповедь культа дыма
	g = Image.new("RGB", (W, H), (60, 60, 64))
	gd = ImageDraw.Draw(g)
	for k in range(30):
		r = 40 + k * 22
		gd.ellipse((W // 2 - r, 480 - r, W // 2 + r, 480 + r), outline=(90 + k * 2, 90 + k * 2, 96 + k * 2), width=10)
	im.paste(g)
	center_text(d, W, 60, "Der Dunst\nist kein Feind", "fraktur", 96, (235, 235, 230))
	d.ellipse((W // 2 - 90, 390, W // 2 + 90, 570), outline=(235, 235, 230), width=6)  # «око дыма»
	d.ellipse((W // 2 - 30, 450, W // 2 + 30, 510), fill=(235, 235, 230))
	for k in range(12):
		a = math.pi * k / 6
		d.line((W // 2 + 110 * math.cos(a), 480 + 110 * math.sin(a), W // 2 + 160 * math.cos(a), 480 + 160 * math.sin(a)), fill=(235, 235, 230), width=5)
	y = center_text(d, W, 640, "Die Felder trennen uns\nvom Heil.", "playfair", 52, (240, 240, 235))
	center_text(d, W, y + 40, "Versammlung im Nebel —\nwenn die Sirene schweigt.\nKommt ohne Maske.", "type", 34, (220, 220, 215))
	center_text(d, W, H - 110, "~ Gemeinde des Grauen Atems ~", "cinzel", 30, (200, 200, 195))


def f_trade(im, d, W, H):          # «тауш»: меняю консервы на фильтры
	d.rectangle((30, 30, W - 30, H - 30), outline=INK, width=3)
	center_text(d, W, 70, "TAUSCHE", "bangers", 120, (30, 90, 40))
	y = center_text(d, W, 240, "Konserven (Erbsen, Ravioli)\ngegen FILTER Typ A2\noder Batterien 9V", "type", 40, INK)
	center_text(d, W, y + 60, "Nachricht hinter der Theke\nim NEON lassen — bei Farah.", "lobster", 46, (40, 40, 120))
	for k in range(9):
		x = 50 + k * (W - 100) // 9
		d.line((x, H - 230, x, H - 30), fill=(120, 120, 120), width=2)


def f_gang(im, d, W, H):           # предупреждение бандитов
	im.paste((240, 240, 235), (0, 0, W, H))
	t = Image.new("RGBA", (W, H), (0, 0, 0, 0))
	td = ImageDraw.Draw(t)
	td.text((40, 80), "SCHUTZGELD", font=fnt("bangers", 140), fill=(200, 20, 20, 255))
	td.text((60, 330), "Freitag. Kein Aufschub.", font=fnt("oswald", 64), fill=(20, 20, 20, 255))
	td.text((60, 460), "— die Jungs vom Kanal", font=fnt("type", 48), fill=(20, 20, 20, 255))
	t = t.rotate(-6, resample=Image.BICUBIC)
	im.paste(t, (0, 0), t)
	d.rectangle((W // 2 - 140, 650, W // 2 + 140, 950), outline=(200, 20, 20), width=14)   # отпечаток ладони — рамка-знак
	for k in range(5):
		d.rounded_rectangle((W // 2 - 110 + k * 46, 680 + abs(2 - k) * 30, W // 2 - 80 + k * 46, 820), 12, fill=(200, 20, 20))
	d.ellipse((W // 2 - 110, 780, W // 2 + 110, 930), fill=(200, 20, 20))


def f_concert(im, d, W, H):        # старая афиша вечеринки
	for k in range(0, H, 40):
		d.rectangle((0, k, W, k + 20), fill=(255, 90, 160) if (k // 40) % 2 else (40, 220, 220))
	d.rectangle((50, 220, W - 50, H - 220), fill=(15, 10, 30))
	center_text(d, W, 280, "NEON", "monoton", 150, (255, 90, 200))
	y = center_text(d, W, 520, "80er · 90er · Ruhrpott-Hits", "oswald", 52, (230, 230, 240))
	center_text(d, W, y + 40, "SAMSTAG · bis der Strom geht", "bebas", 64, (40, 220, 220))


def f_missing(im, d, W, H):        # «Кто видел Калле?»
	center_text(d, W, 60, "WER HAT\nKALLE GESEHEN?", "anton", 88, INK)
	d.rectangle((120, 330, W - 120, 760), fill=(170, 165, 150), outline=INK, width=4)
	d.ellipse((W // 2 - 110, 380, W // 2 + 110, 600), fill=(90, 80, 70))               # фото-силуэт с каской
	d.pieslice((W // 2 - 140, 340, W // 2 + 140, 560), 180, 360, fill=(230, 190, 30))
	d.rectangle((W // 2 - 170, 600, W // 2 + 170, 760), fill=(70, 70, 75))
	center_text(d, W, 800, "Steiger, 58 Jahre, Schacht 3.\nZuletzt am Tunnel U21.\nFunkfrequenz 27,1 MHz", "type", 38, INK)


def f_liquid(im, d, W, H):         # ликвидаторы: набор добровольцев
	d.rectangle((0, 0, W, H), fill=(230, 200, 40))
	d.rectangle((40, 40, W - 40, H - 40), outline=INK, width=8)
	center_text(d, W, 90, "FELDTRUPP", "anton", 110, INK)
	center_text(d, W, 240, "sucht Helfer", "lobster", 80, INK)
	for k in range(6):
		d.line((80, 420 + k * 18, W - 80, 420 + k * 18), fill=INK, width=4)
	y = center_text(d, W, 560, "Kabel · Sicherungen · Hände\nBezahlung in Filtern\nTreff: Pylon 7, Neumarkt", "type", 40, INK)
	center_text(d, W, H - 140, "!! NICHT ALLEIN KOMMEN !!", "oswald", 40, (160, 20, 20))


FLYERS = [("flyer_power", (720, 1020), (240, 238, 230), f_power), ("flyer_cat", (720, 1020), (250, 250, 245), f_cat),
	("flyer_cult", (720, 1020), (60, 60, 64), f_cult), ("flyer_trade", (720, 960), (245, 240, 225), f_trade),
	("flyer_gang", (720, 1020), (240, 240, 235), f_gang), ("flyer_concert", (720, 1020), (20, 10, 30), f_concert),
	("flyer_missing", (720, 1020), (235, 232, 220), f_missing), ("flyer_liquid", (720, 1020), (230, 200, 40), f_liquid)]
for i, (n, s, bg, fn) in enumerate(FLYERS):
	flyer(n, s, bg, fn, 100 + i)

# --- рваные слои старых афиш (большой фрагмент стены, прозрачный фон) -------------------------
W, H = 2048, 1536
im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
cols = [(200, 40, 40), (240, 220, 40), (30, 60, 140), (240, 240, 235), (20, 20, 25), (255, 120, 180), (40, 180, 180)]
words = ["NEON", "LIVE", "BLAU WEISS", "SCHICHT", "DERBY", "KORN", "PILS", "TANZ", "FREITAG", "GRUBE", "04", "NEBEL"]
for k in range(34):
	w, h = rnd.randint(380, 900), rnd.randint(500, 1100)
	layer = Image.new("RGB", (w, h), rnd.choice(cols))
	ld = ImageDraw.Draw(layer)
	for _ in range(3):
		ld.text((rnd.randint(-40, w // 3), rnd.randint(0, h - 200)), rnd.choice(words), font=fnt(rnd.choice(["bangers", "anton", "bebas", "rye"]), rnd.randint(120, 260)),
			fill=rnd.choice(cols))
	layer = age(layer, k, 0.6).convert("RGBA")
	a = torn_alpha(w, h, 300 + k, 60)
	# дыры: часть верхнего слоя сорвана
	ad = ImageDraw.Draw(a)
	for _ in range(rnd.randint(1, 4)):
		x, y, rr = rnd.randrange(w), rnd.randrange(h), rnd.randint(60, 260)
		pts = [(x + rr * math.cos(t) * rnd.uniform(0.5, 1.2), y + rr * math.sin(t) * rnd.uniform(0.5, 1.2)) for t in [i * math.pi / 8 for i in range(16)]]
		ad.polygon(pts, fill=0)
	layer.putalpha(a)
	layer = layer.rotate(rnd.uniform(-6, 6), expand=True, resample=Image.BICUBIC)
	im.alpha_composite(layer, (rnd.randint(-200, W - 300), rnd.randint(-200, H - 300)))
# общая маска: края фрагмента рваные
mask = torn_alpha(W, H, 999, 140)
alpha = Image.composite(im.getchannel("A"), Image.new("L", (W, H), 0), mask)
im.putalpha(alpha)
im.save(f"{OUT}/torn_layers.png")

# --- картон, фанера, скотч ------------------------------------------------------------------
W, H = 1024, 1024
im = Image.new("RGB", (W, H), (165, 125, 80))
d = ImageDraw.Draw(im)
for y in range(0, H, 9):
	d.line((0, y, W, y), fill=(150, 112, 70), width=3)
d.text((120, 380), "ZERBRECHLICH", font=fnt("anton", 110), fill=(60, 40, 25))
d.text((140, 520), "OBEN · Konserven 24 Stk.", font=fnt("type", 56), fill=(60, 40, 25))
age(im, 7, 1.4).save(f"{OUT}/cardboard.png")
im = Image.new("RGB", (W, H), (190, 160, 115))
d = ImageDraw.Draw(im)
for k in range(120):
	y = rnd.randrange(H)
	d.arc((rnd.randint(-400, W), y - 60, rnd.randint(W, W + 800), y + 60), 180, 360, fill=(170, 135, 90), width=rnd.randint(2, 6))
for (x, y) in [(40, 40), (W - 60, 40), (40, H - 60), (W - 60, H - 60), (W // 2, 40), (W // 2, H - 60)]:
	d.ellipse((x, y, x + 18, y + 18), fill=(70, 70, 75))
t = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(t).text((90, 380), "BETRETEN\nVERBOTEN", font=fnt("bangers", 190), fill=(200, 30, 30, 220))
t = t.rotate(8, resample=Image.BICUBIC)
im.paste(t, (0, 0), t)
age(im, 8, 1.2).save(f"{OUT}/plywood.png")
im = Image.new("RGBA", (512, 128), (200, 200, 195, 200))
d = ImageDraw.Draw(im)
for x in range(0, 512, 6):
	d.line((x, 0, x, 128), fill=(180, 180, 175, 200), width=1)
im.putalpha(torn_alpha(512, 128, 77, 10, "lr"))
im.save(f"{OUT}/tape.png")
print("ok")
