# Каталог новых загрузок автора (превью от сессии на ПК).
# python3 make_catalog_incoming.py [сводка.json выход.png] -> по умолчанию incoming_2026-10-10.json -> catalog_incoming.png
import json, os, sys
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
INC = os.path.join(HERE, "assets_preview", "incoming")
SRC = sys.argv[1] if len(sys.argv) > 1 else "incoming_2026-10-10.json"
OUT = sys.argv[2] if len(sys.argv) > 2 else "catalog_incoming.png"
d = json.load(open(os.path.join(INC, SRC), encoding="utf-8"))
SEEN = set(json.load(open(os.path.join(INC, "incoming_2026-10-10.json"), encoding="utf-8"))["items"][i]["id"] for i in range(5)) if SRC != "incoming_2026-10-10.json" else set()
TITLE = "Новые загрузки автора 09–10.10 — одежда и персонаж" if not SEEN else "Загрузки 10.10 — вещи и декали (REPEAT ON MAP, RARE PROP)"
F, FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
f_t, f_b, f_s, f_h = ImageFont.truetype(FB, 21), ImageFont.truetype(F, 15), ImageFont.truetype(F, 14), ImageFont.truetype(FB, 28)
VER = {"ПОДОГНАТЬ": (255, 200, 60), "РЕТОПОЛОГИЯ": (255, 140, 60), "ЛИЦЕНЗИЯ?": (150, 190, 255), "CC-ЛИЦЕНЗИЯ": (150, 190, 255), "РЕТАРГЕТ": (255, 200, 60), "ГОТОВО": (120, 220, 130), "МАСШТАБ": (255, 200, 60), "МАТЕРИАЛ": (255, 170, 90), "ДЕКАЛЬ": (120, 200, 240)}
# вердикт и короткая заметка по каждой позиции
NOTE = {"futuristic_top": ("ПОДОГНАТЬ", "Лёгкая (2,5 тыс.), 2K PBR — хороша для НПС; посадить на тело и перенести веса"),
	"streetwear_sweatshirt": ("ПОДОГНАТЬ", "Унисекс, 4K — для героя и жителей; посадить на тело, текстуры для НПС ужать до 2K"),
	"dress_elegant": ("ПОДОГНАТЬ", "Платье для NEON/лаунжа; 19 тыс. — норма для героя; UDIM 1001 → обычная развёртка"),
	"shorts_scan": ("РЕТОПОЛОГИЯ", "1,5 млн треугольников и нет текстур — в игру только после ретопологии до 10–20 тыс."),
	"old_book": ("МАСШТАБ", "Редкая находка: фотоальбом/дневник для заданий жителей; ×0,19 до 22×30 см, 352 треуг. — дёшево"),
	"plastic_bin_blue": ("РЕТОПОЛОГИЯ", "Ходовая мусорка для дворов, офисов, Späti; 500 тыс. → 1–2 тыс. треуг., текстура ИИ — проверить швы"),
	"locker": ("ГОТОВО", "Шкафчики на 3 и на 1 дверцу, полный PBR: раздевалки клуба, депо ликвидаторов, вокзал; можно сделать лут-контейнером"),
	"hospital_bed": ("ГОТОВО", "Железная кровать с матрасом и одеялом: квартиры затворников, лазарет ликвидаторов, хаб; 16 тыс. — уменьшить LOD"),
	"tv_crt": ("МАСШТАБ", "Ламповый ТВ: квартиры, бар, хаб, мусор у домов; ×0,16; можно светящийся экран (помехи) при дефиците света"),
	"door": ("МАТЕРИАЛ", "Дверь подъезда/квартиры, исходник в см (×0,01); текстур нет — свой материал (краска + износ)"),
	"wooden_pallet": ("ГОТОВО", "Европоддон уже в игре: assets/props/fab_wooden_pallet — баррикады, склады, Kaufhof, костры"),
	"dirty_papers": ("ДЕКАЛЬ", "Разбросанные бумаги, 4K, 10 карт: декаль на пол вокзала, ратуши, улиц; для игры 2K + альфа"),
	"garbage_pile": ("ДЕКАЛЬ", "Куча мусора 1×1 м, 4K: у стен, в переулках, у Späti; декаль или плоскость с рельефом"),
	"garbage_pile_small": ("ДЕКАЛЬ", "Малая куча 0,5 м: углы, урны, лестницы, туалеты клуба"),
	"joy_character": ("РЕТАРГЕТ", "Персонаж Character Creator (CC0): скелет CC_Base (как у Фарах) — перенести анимации или переименовать кости под Mixamo; жилет и бельё сидят на теле CC")}
cards = []
for x in d["items"]:
	if x["id"] in SEEN:
		continue
	prev = [p.strip() for p in str(x.get("preview", "")).split(",") if p.strip()]
	ver, note = NOTE.get(x["id"], ("ЛИЦЕНЗИЯ?", ""))
	cards.append((prev, x, ver, note))
CW, CH, IMG = 1020, 330, 270
H = 120 + len(cards) * CH + 20
S = Image.new("RGB", (CW + 40, H), (20, 20, 26))
dr = ImageDraw.Draw(S)
dr.text((24, 22), TITLE, font=f_h, fill=(235, 235, 240))
dr.text((24, 62), "Превью — сессия на ПК, модели остаются на ПК. Лицензия — CC0 (подтвердил автор): коммерческая игра, без указания автора.", font=f_s, fill=(170, 170, 180))
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
	lines = [(x["name"], f_t, (240, 240, 245)), (x["type"], f_b, (225, 225, 230)), (f"{x['format']} · {int(x['triangles']):,} треуг.".replace(",", " "), f_b, (170, 170, 185)),
		("Текстуры: " + str(x["textures"]), f_b, (170, 170, 185)), ("Скелет: " + str(x["skeleton"]), f_b, (170, 170, 185)),
		("Куда: " + str(x.get("fits", "—")) + (" · " + x["size_note"] if x.get("size_note") else ""), f_b, (200, 200, 230)),
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
S.save(os.path.join(HERE, "assets_preview", OUT))
print("ok", S.size)
