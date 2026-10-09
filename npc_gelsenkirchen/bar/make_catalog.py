# Каталог кандидатов на импорт (картинки + оценка). python3 make_catalog.py <превью Khronos> <лист Poly Haven> <out.png>
import sys, json
from PIL import Image, ImageDraw, ImageFont
prev, ph_sheet, out = sys.argv[1], sys.argv[2], sys.argv[3]
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
f_t, f_b, f_s, f_h = ImageFont.truetype(FB, 22), ImageFont.truetype(F, 16), ImageFont.truetype(F, 14), ImageFont.truetype(FB, 30)
info = json.load(open(prev + "/info.json"))
VER = {"БРАТЬ": (90, 220, 120), "ПЕРЕКРАСИТЬ": (255, 200, 60), "МОЖНО": (150, 190, 255), "НЕ БРАТЬ": (255, 90, 90)}
K = [  # id, назначение, вердикт, лицензия, примечание
	("CommercialRefrigerator", "Холодильник-витрина: задняя стенка бара, кухня", "БРАТЬ", "CC-BY 4.0", "очень детальный; для игры — упростить сетку (LOD)"),
	("SheenWoodLeatherSofa", "Диван кожа+дерево: 3 приватные комнаты", "БРАТЬ", "CC-BY / CC0", "потёртая кожа — в стиль подвала"),
	("AnisotropyBarnLamp", "Медное бра: кирпич у сцены и в лаунже", "БРАТЬ", "CC-BY 4.0", "реалистичная анизотропная медь"),
	("IridescentDishWithOlives", "Закуски под колпаком: стойка бара", "БРАТЬ", "CC-BY 4.0", "стекло и металл, 2K"),
	("DiffuseTransmissionPlant", "Растение в кадке: лаунж, площадка", "БРАТЬ", "CC-BY / CC0", "просвечивающие листья; сетку упростить"),
	("GlassBrokenWindow", "Разбитое окно: за досками (лор «Карантин»)", "БРАТЬ", "CC-BY 4.0", "раму перекрасить в тёмный металл"),
	("GlamVelvetSofa", "Бархатный диван: лаунж 2 этажа", "ПЕРЕКРАСИТЬ", "CC-BY 4.0", "голубой → тёмно-синий «Blau-Weiß»"),
	("SheenChair", "Кресло: лаунж", "ПЕРЕКРАСИТЬ", "CC0", "розовый → тёмная кожа или бархат"),
	("SpecularSilkPouf", "Пуф: приватные комнаты", "ПЕРЕКРАСИТЬ", "CC-BY 4.0", "розовый → бордо; сетку упростить"),
	("IridescenceLamp", "Настольная лампа: приватные комнаты", "МОЖНО", "CC-BY 4.0", "абажур можно затемнить"),
	("GlassVaseFlowers", "Цветы в вазе: столики 2 этажа", "МОЖНО", "CC0", "мелкая, хорошо смотрится вблизи"),
	("ChairDamaskPurplegold", "Стул с дамаском", "НЕ БРАТЬ", "CC-BY 4.0", "не наш стиль, текстуры всего 1K"),
]
# Poly Haven: (id, колонка, строка) в листе docs/texture_candidates_polyhaven.png (3 × 9, ячейка 256 × 290)
P = [
	("dark_brick_wall", 0, 2, "Тёмный кирпич: стены зала (4K — за баром)", "БРАТЬ"),
	("concrete_floor_worn_001", 0, 4, "Потёртый бетон: пол 1 этажа", "БРАТЬ"),
	("weathered_planks", 0, 1, "Старые доски: заколоченные окна", "БРАТЬ"),
	("worn_cracked_plaster", 0, 3, "Штукатурка: стены приватных комнат", "МОЖНО"),
	("medieval_red_brick", 2, 2, "Красный кирпич: запасной вариант стен", "МОЖНО"),
]
cards = []
for kid, use, ver, lic, note in K:
	i = info[kid]
	cards.append((Image.open(f"{prev}/{kid}.png"), kid, use, ver,
		[f"Khronos glTF Sample Assets · {lic}", f"{i['tris']:,} треуг. · текстуры до {i['max_tex'][0]}×{i['max_tex'][1]}".replace(",", " "),
		f"размер {i['dims_m'][0]}×{i['dims_m'][1]}×{i['dims_m'][2]} м", note]))
sheet = Image.open(ph_sheet)
for pid, c, r, use, ver in P:
	cards.append((sheet.crop((c * 256, r * 290, c * 256 + 256, r * 290 + 256)), pid, use, ver,
		["Poly Haven · CC0 (автор не обязателен)", "набор 4K: цвет, нормаль, шероховатость, AO", "качает сессия на ПК (сайт закрыт из облака)", "превью — лист проекта"]))
CW, CH, IMG, COLS = 760, 300, 270, 2
rows = (len(cards) + COLS - 1) // COLS
W, H = CW * COLS + 40, 120 + rows * CH + 20
S = Image.new("RGB", (W, H), (20, 20, 26))
d = ImageDraw.Draw(S)
d.text((24, 22), "Клуб «Neon» — кандидаты на импорт (рендер в Blender, студийный свет)", font=f_h, fill=(235, 235, 240))
d.text((24, 66), "Модели Khronos скачаны только во временную папку для превью — в проект ничего не импортировано. "
	"Зелёный — брать, жёлтый — брать с перекраской, синий — по желанию, красный — не брать.", font=f_s, fill=(170, 170, 180))
for n, (im, cid, use, ver, lines) in enumerate(cards):
	x, y = 20 + (n % COLS) * CW, 110 + (n // COLS) * CH
	d.rectangle((x, y, x + CW - 20, y + CH - 16), fill=(30, 30, 38), outline=(55, 55, 70))
	t = im.convert("RGB").resize((IMG, IMG))
	S.paste(t, (x + 8, y + 8))
	tx = x + IMG + 24
	d.rectangle((tx, y + 14, tx + 12 + d.textlength(ver, font=f_s), y + 36), fill=VER[ver])
	d.text((tx + 6, y + 16), ver, font=f_s, fill=(15, 15, 15))
	d.text((tx, y + 46), cid, font=f_t, fill=(240, 240, 245))
	yy = y + 80
	for ln in [use] + lines:
		# перенос строк по ширине
		words, cur = ln.split(), ""
		for w_ in words:
			if d.textlength(cur + " " + w_, font=f_b) > CW - IMG - 60:
				d.text((tx, yy), cur, font=f_b, fill=(225, 225, 230) if ln == use else (170, 170, 185)); yy += 22; cur = w_
			else:
				cur = (cur + " " + w_).strip()
		d.text((tx, yy), cur, font=f_b, fill=(225, 225, 230) if ln == use else (170, 170, 185)); yy += 26
S.save(out)
print(out, S.size)
