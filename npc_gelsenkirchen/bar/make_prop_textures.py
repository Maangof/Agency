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


# --- этикетки бутылок (развёртка по окружности: 2048 × 512, этикетка — в середине) ------
LABELS = [
	("label_korn", "GELSEN KORN", "Doppelkorn · 38 % vol", "seit 1923 · Revier-Brennerei", (236, 228, 205), (30, 60, 140), (180, 30, 30)),
	("label_kraeuter", "KOHLENPOTT", "Kräuterlikör · 35 % vol", "56 Kräuter aus dem Schacht", (25, 60, 35), (230, 200, 90), (230, 200, 90)),
	("label_rum", "SCHICHT RUM", "Dark · 40 % vol", "nach der Schicht · ein Schluck", (40, 25, 15), (220, 170, 80), (220, 170, 80)),
	("label_gin", "REVIER GIN", "Dry Gin · 41 % vol", "Wacholder & Grubengrün", (230, 238, 240), (20, 90, 110), (20, 90, 110)),
	("label_vodka", "ZOLLVEREIN", "Wodka · 40 % vol", "klar wie Grubenwasser", (245, 245, 248), (30, 30, 35), (120, 120, 130)),
	("label_whisky", "HALDE 12", "Single Malt · 43 % vol", "12 Jahre unter Tage gereift", (200, 160, 90), (60, 30, 10), (60, 30, 10)),
]
for name, title, sub, small, bg, fg, acc in LABELS:
	W, H = 2048, 512
	im = Image.new("RGB", (W, H), bg)
	d = ImageDraw.Draw(im)
	x0, x1 = 640, 1408                       # лицевая часть
	d.rectangle((x0, 24, x1, H - 24), outline=acc, width=6)
	d.rectangle((x0 + 14, 38, x1 - 14, H - 38), outline=fg, width=2)
	ft = font(SERIF_B, 96 if len(title) < 10 else 74)
	tw = d.textlength(title, font=ft)
	d.text((x0 + (x1 - x0 - tw) / 2, 150), title, font=ft, fill=fg)
	fs = font(SERIF, 44)
	sw = d.textlength(sub, font=fs)
	d.text((x0 + (x1 - x0 - sw) / 2, 280), sub, font=fs, fill=acc)
	fsm = font(SANS, 30)
	smw = d.textlength(small, font=fsm)
	d.text((x0 + (x1 - x0 - smw) / 2, 360), small, font=fsm, fill=fg)
	# эмблема: молот и кирка (шахтёрский знак) — двумя линиями
	cx, cy = (x0 + x1) / 2, 95
	d.line((cx - 34, cy - 30, cx + 34, cy + 30), fill=acc, width=9)
	d.line((cx + 34, cy - 30, cx - 34, cy + 30), fill=acc, width=9)
	# задняя этикетка: штрихкод и мелкий текст
	for k in range(40):
		w_ = rnd.choice((2, 3, 5))
		d.rectangle((1600 + k * 7, 300, 1600 + k * 7 + w_, 420), fill=fg)
	d.text((1560, 120), "Hergestellt in Gelsenkirchen\nQuarantäne-Abfüllung · 0,7 l", font=font(SANS, 28), fill=fg)
	im = paper_noise(im, 10, hash(name) % 1000).filter(ImageFilter.GaussianBlur(0.6))
	im.save(f"{OUT}/{name}.png")

# пивная этикетка (0,33 «Stubbi»)
W, H = 1024, 384
im = Image.new("RGB", (W, H), (240, 232, 210))
d = ImageDraw.Draw(im)
d.rectangle((300, 20, 724, H - 20), fill=(20, 50, 130))
d.rectangle((312, 32, 712, H - 32), outline=(240, 232, 210), width=4)
centered(d, 70, "ZECHE", font(SERIF_B, 70), (240, 232, 210), W)
centered(d, 150, "PILS", font(SERIF_B, 110), (255, 255, 255), W)
centered(d, 290, "Blau-Weiß Bräu · 4,9 %", font(SANS, 28), (240, 232, 210), W)
paper_noise(im, 8, 7).save(f"{OUT}/label_beer.png")

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

# --- постеры (A1-пропорции 1024 × 1448) -------------------------------------------------
def poster(name, bg, lines, frame=(255, 255, 255), seed=1):
	W, H = 1024, 1448
	im = Image.new("RGB", (W, H), bg)
	d = ImageDraw.Draw(im)
	r = random.Random(seed)
	for spec in lines:
		kind = spec[0]
		if kind == "t":
			_, y, text, path, size, col = spec
			centered(d, y, text, font(path, size), col, W)
		elif kind == "rect":
			_, box_, col = spec
			d.rectangle(box_, fill=col)
		elif kind == "circle":
			_, box_, col, w = spec
			d.ellipse(box_, outline=col, width=w)
	# потёртость, сгибы, скотч по углам
	d.line((0, H // 2, W, H // 2 + 6), fill=tuple(max(0, c - 25) for c in bg), width=3)
	d.line((W // 2, 0, W // 2 - 4, H), fill=tuple(max(0, c - 20) for c in bg), width=2)
	for (x, y) in [(20, 20), (W - 150, 20), (20, H - 70), (W - 150, H - 70)]:
		d.rectangle((x, y, x + 130, y + 50), fill=(230, 225, 200))
	im = paper_noise(im, 22, seed).filter(ImageFilter.GaussianBlur(0.7))
	im.save(f"{OUT}/{name}.png")


poster("poster_rocknight", (15, 15, 20), [
	("rect", (60, 160, 964, 900), (180, 20, 40)),
	("circle", (312, 640, 712, 860), (255, 230, 80), 0),
	("t", 420, "KUMPEL", SANS_B, 150, (255, 230, 80)),
	("t", 580, "ROCK NIGHT", SANS_B, 110, (255, 255, 255)),
	("t", 960, "LIVE IM NEON · FREITAG 22 UHR", CONDB, 56, (255, 255, 255)),
	("t", 1050, "Die Steiger · Halde 9 · Grubengas", SANS, 46, (200, 200, 210)),
	("t", 1200, "Eintritt nur mit Passierschein", SERIF, 40, (255, 120, 120))], seed=11)
poster("poster_derby", (240, 240, 245), [
	("rect", (0, 0, 1024, 420), (20, 50, 130)),
	("t", 90, "BLAU-WEISS 04", SANS_B, 110, (255, 255, 255)),
	("t", 250, "DAS DERBY", SANS_B, 90, (160, 200, 255)),
	("t", 520, "Großbildleinwand", SERIF_B, 80, (20, 50, 130)),
	("t", 640, "Samstag · 15:30", SANS_B, 70, (20, 20, 25)),
	("t", 800, "Jedes Tor: Runde Korn", SERIF, 60, (180, 30, 30)),
	("t", 1180, "Nur echte Kumpel. Kein Gegner-Schal!", SANS, 40, (60, 60, 70))], seed=12)
poster("poster_maske", (235, 225, 40), [
	("rect", (60, 60, 964, 1388), (20, 20, 20)),
	("rect", (80, 80, 944, 1368), (235, 225, 40)),
	("t", 160, "ACHTUNG", SANS_B, 140, (20, 20, 20)),
	("t", 420, "NUR MIT", SANS_B, 120, (20, 20, 20)),
	("t", 560, "MASKE", SANS_B, 170, (180, 20, 20)),
	("t", 760, "TANZEN!", SANS_B, 140, (20, 20, 20)),
	("t", 1020, "Quarantäne-Verordnung §04", SERIF, 46, (40, 40, 40)),
	("t", 1090, "GelsenOS wünscht viel Spaß", SERIF, 40, (40, 40, 40))], seed=13)
poster("poster_lastcall", (25, 10, 35), [
	("t", 200, "SCHICHT", SANS_B, 150, (255, 80, 180)),
	("t", 380, "IM SCHACHT", SANS_B, 110, (255, 80, 180)),
	("circle", (312, 600, 712, 1000), (120, 200, 255), 14),
	("t", 740, "03:00", SANS_B, 110, (120, 200, 255)),
	("t", 1120, "Letzte Runde · letzte Bahn 301", CONDB, 50, (230, 230, 240)),
	("t", 1200, "Wer den Nebel sieht, geht heim.", SERIF, 40, (180, 180, 200))], seed=14)

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
