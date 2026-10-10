# Каталог новых загрузок автора (превью от сессии на ПК). python3 make_catalog_incoming.py -> assets_preview/catalog_incoming.png
import json, os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
INC = os.path.join(HERE, "assets_preview", "incoming")
d = json.load(open(os.path.join(INC, "incoming_2026-10-10.json"), encoding="utf-8"))
F, FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
f_t, f_b, f_s, f_h = ImageFont.truetype(FB, 21), ImageFont.truetype(F, 15), ImageFont.truetype(F, 14), ImageFont.truetype(FB, 28)
VER = {"ПОДОГНАТЬ": (255, 200, 60), "РЕТОПОЛОГИЯ": (255, 140, 60), "ЛИЦЕНЗИЯ?": (150, 190, 255), "CC-ЛИЦЕНЗИЯ": (150, 190, 255), "РЕТАРГЕТ": (255, 200, 60)}
# вердикт и короткая заметка по каждой позиции
NOTE = {"futuristic_top": ("ПОДОГНАТЬ", "Лёгкая (2,5 тыс.), 2K PBR — хороша для НПС; посадить на тело и перенести веса"),
	"streetwear_sweatshirt": ("ПОДОГНАТЬ", "Унисекс, 4K — для героя и жителей; посадить на тело, текстуры для НПС ужать до 2K"),
	"dress_elegant": ("ПОДОГНАТЬ", "Платье для NEON/лаунжа; 19 тыс. — норма для героя; UDIM 1001 → обычная развёртка"),
	"shorts_scan": ("РЕТОПОЛОГИЯ", "1,5 млн треугольников и нет текстур — в игру только после ретопологии до 10–20 тыс."),
	"joy_character": ("РЕТАРГЕТ", "Персонаж Character Creator (CC0): скелет CC_Base (как у Фарах) — перенести анимации или переименовать кости под Mixamo; жилет и бельё сидят на теле CC")}
cards = []
for x in d["items"]:
	prev = [p.strip() for p in str(x.get("preview", "")).split(",") if p.strip()]
	ver, note = NOTE.get(x["id"], ("ЛИЦЕНЗИЯ?", ""))
	cards.append((prev, x, ver, note))
CW, CH, IMG = 1020, 300, 270
H = 120 + len(cards) * CH + 20
S = Image.new("RGB", (CW + 40, H), (20, 20, 26))
dr = ImageDraw.Draw(S)
dr.text((24, 22), "Новые загрузки автора 09–10.10 — одежда и персонаж", font=f_h, fill=(235, 235, 240))
dr.text((24, 62), "Превью — сессия на ПК (модели остаются на ПК). Лицензия у всех — CC0 (подтвердил автор): можно в коммерческую игру, автора указывать не обязательно.", font=f_s, fill=(170, 170, 180))
for n, (prev, x, ver, note) in enumerate(cards):
	y = 105 + n * CH
	dr.rectangle((20, y, 20 + CW, y + CH - 16), fill=(30, 30, 38), outline=(55, 55, 70))
	xx = 28
	for p in prev[:3]:
		pp = os.path.join(INC, p)
		if os.path.exists(pp):
			S.paste(Image.open(pp).convert("RGB").resize((IMG, IMG)), (xx, y + 8))
			xx += IMG + 6
	tx = 28 + IMG + 16 if len(prev) <= 1 else xx + 10
	wmax = 20 + CW - tx - 14
	dr.rectangle((tx, y + 14, tx + 12 + dr.textlength(ver, font=f_s), y + 36), fill=VER[ver])
	dr.text((tx + 6, y + 16), ver, font=f_s, fill=(15, 15, 15))
	lines = [(x["name"], f_t, (240, 240, 245)), (x["type"], f_b, (225, 225, 230)), (f"{x['format']} · {x['triangles']:,} треуг.".replace(",", " "), f_b, (170, 170, 185)),
		("Текстуры: " + str(x["textures"]), f_b, (170, 170, 185)), ("Скелет: " + str(x["skeleton"]), f_b, (170, 170, 185)),
		("Лицензия: " + str(x["license"]), f_b, (140, 220, 150)), (note, f_b, (200, 225, 200))]
	yy = y + 46
	for text, fnt, col in lines:
		words, cur = str(text).split(), ""
		for w in words:
			if dr.textlength(cur + " " + w, font=fnt) > wmax:
				dr.text((tx, yy), cur, font=fnt, fill=col); yy += 20; cur = w
			else:
				cur = (cur + " " + w).strip()
		dr.text((tx, yy), cur, font=fnt, fill=col); yy += 23
S.save(os.path.join(HERE, "assets_preview", "catalog_incoming.png"))
print("ok", S.size)
