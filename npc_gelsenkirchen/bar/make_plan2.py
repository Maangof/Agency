# Схема клуба «Neon» в 2 этажа (вид сверху, в масштабе). python3 make_plan2.py -> club2_plan.svg
# Координаты — как в Godot / build_club2.py: x восток, -z север; зал 16 × 12, кухня — пристройка к северу.
import math
S = 38
OUT = []
COLL, DECOR, WALLC = "#5a3a22", "#3a3f55", "#8888a0"
FONT = 'font-family="Arial, sans-serif"'


class Plan:
	def __init__(self, ox, oy, zmin):
		self.ox, self.oy, self.zmin = ox, oy, zmin

	def X(self, x):
		return self.ox + (x + 8) * S

	def Y(self, z):
		return self.oy + (z - self.zmin) * S

	def rect(self, x0, z0, x1, z1, fill, stroke="none", sw=1, extra=""):
		OUT.append(f'<rect x="{self.X(min(x0, x1)):.1f}" y="{self.Y(min(z0, z1)):.1f}" width="{abs(x1 - x0) * S:.1f}" '
			f'height="{abs(z1 - z0) * S:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')

	def circ(self, x, z, r, fill, stroke="none", sw=1):
		OUT.append(f'<circle cx="{self.X(x):.1f}" cy="{self.Y(z):.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

	def line(self, x0, z0, x1, z1, color, sw=2, extra=""):
		OUT.append(f'<line x1="{self.X(x0):.1f}" y1="{self.Y(z0):.1f}" x2="{self.X(x1):.1f}" y2="{self.Y(z1):.1f}" stroke="{color}" stroke-width="{sw}" {extra}/>')

	def txt(self, x, z, s, size=11, fill="#e8e8f0", weight="normal", anchor="middle", rot=0):
		tr = f' transform="rotate({rot} {self.X(x):.1f} {self.Y(z):.1f})"' if rot else ""
		OUT.append(f'<text x="{self.X(x):.1f}" y="{self.Y(z):.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
			f'font-weight="{weight}" {FONT}{tr}>{s}</text>')

	def spot(self, x, z, label, color="#ffd23f"):
		self.circ(x, z, 8, color, "#111", 1.5)
		self.txt(x, z + 0.09, label, 9, "#111", "bold")

	def grid(self, x0, z0, x1, z1):
		for i in range(math.ceil(x0), math.floor(x1) + 1):
			self.line(i, z0, i, z1, "#22222c", 1)
		for j in range(math.ceil(z0), math.floor(z1) + 1):
			self.line(x0, j, x1, j, "#22222c", 1)

	def door(self, x, z, horizontal=True, w=0.9, color="#7dff9a"):
		if horizontal:
			self.line(x - w / 2, z, x + w / 2, z, color, 4)
		else:
			self.line(x, z - w / 2, x, z + w / 2, color, 4)


def text_px(x, y, s, size=12, fill="#e8e8f0", weight="normal", anchor="start"):
	OUT.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" {FONT}>{s}</text>')


M = 40
TITLE_H = 70
W_PLAN = 16 * S
p1 = Plan(M, TITLE_H + 44, -10.0)                 # 1 этаж + кухня (z -10..6)
p2 = Plan(M + W_PLAN + 70, TITLE_H + 44 + 4 * S, -6.0)   # 2 этаж (z -6..6), низ выровнен с 1 этажом
TOT_W = M * 2 + W_PLAN * 2 + 70
TOT_H = TITLE_H + 44 + 16 * S + 230

OUT.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {TOT_W} {TOT_H}" width="{TOT_W}" height="{TOT_H}">')
OUT.append('<rect width="100%" height="100%" fill="#14141a"/>')
text_px(M, 34, "КЛУБ «NEON» — 2 ЭТАЖА, вид сверху. 1 клетка = 1 м", 20, weight="bold")
text_px(M, 56, "Зал 16 × 12 м как в ClubRoom.gd; стойка и сцена — те же коллизии. Кухня — пристройка к северу (одноэтажная).", 12, "#aaa")

# ================================ 1 ЭТАЖ ================================================
p = p1
text_px(p.X(-8), p.Y(-10) - 24, "1 ЭТАЖ (EG) · пол 0 м, потолок 4 м", 15, "#ffd9b0", "bold")
# кухня
p.grid(-8, -10, -1.5, -6)
p.rect(-8, -10, -1.5, -6, "#2a1c18", WALLC, 4)
p.txt(-4.75, -8.75, "КУХНЯ · Currywurst, Pommes", 13, "#ffb070", "bold")
p.rect(-6.5, -9.95, -2.45, -9.25, DECOR, "#c9a36a"); p.txt(-4.5, -9.5, "плита · фритюр · гриль, вытяжка", 9)
p.rect(-7.95, -9.8, -7.25, -8.6, DECOR, "#c9a36a"); p.txt(-7.6, -8.4, "холод.", 8)
p.rect(-5.8, -8.3, -3.4, -7.5, DECOR, "#c9a36a"); p.txt(-4.6, -7.82, "остров заготовки", 9)
p.rect(-2.15, -9.3, -1.55, -6.95, DECOR, "#c9a36a"); p.txt(-1.85, -8.1, "мойка", 8, rot=-90)
p.rect(-8, -8.1, -7.65, -6.7, DECOR, "#c9a36a")
p.door(-2.45, -10, True, 0.9, "#4cff7a"); p.txt(-2.45, -10.2, "NOTAUSGANG", 9, "#7dff9a")
# зал
p.grid(-8, -6, 8, 6)
p.rect(-8, -6, 8, 6, "#1c1c24", WALLC, 6)
# проём двери кухни и окно выдачи
p.door(-7.2, -6, True, 0.9, "#ffb070")
p.txt(-7.2, -5.65, "КУХНЯ", 9, "#ffb070", "bold")
p.line(-5.4, -6, -4.4, -6, "#ff6040", 5)
p.txt(-4.9, -5.6, "окно выдачи", 9, "#ff9a80")
# сцена
p.rect(1, -5.8, 7, -1.4, "#26263a", "#6aa8ff", 2)
p.txt(4, -3.7, "СЦЕНА  h 0,6", 13, "#9cc4ff", "bold")
p.txt(4, -3.3, "над ней — второй свет (8 м)", 10, "#9cc4ff")
p.rect(4.6, -4.9, 6.2, -4.3, DECOR); p.txt(5.4, -4.5, "пульт", 9)
# стойка, зона работницы
p.rect(-8, -4.4, -7.57, 2.0, DECOR, "#c9a36a", 1)
p.rect(-6.7, -4.7, -5.7, 2.3, COLL, "#ffb070", 2)
p.txt(-6.2, -1.2, "СТОЙКА", 12, "#ffd9b0", "bold", rot=-90)
p.rect(-7.57, -4.7, -6.7, 2.3, "rgba(255,80,180,0.13)", "#ff50b4", 1.5, 'stroke-dasharray="6 4"')
p.circ(-7.25, -1.2, 11, "#ff50b4", "#fff", 2)
p.txt(-7.25, -1.12, "W", 10, "#fff", "bold")
for z in [-4.2, -2.0, -1.2, -0.4, 1.4, 2.0]:
	p.circ(-5.25, z, 7, "#2a4a8a", "#6aa8ff", 1)
p.spot(-4.9, -3.0, "S"); p.spot(-4.9, 0.5, "$"); p.spot(4.0, -0.4, "St"); p.spot(7.2, -0.4, "T")
p.spot(0, 5.6, "E")
# столики
for x, z in [(-2.6, -3.2), (-2.6, -0.2), (0.4, 1.6)]:
	p.circ(x, z, 0.38 * S, DECOR, "#c9a36a", 1)
# туалеты
p.rect(5, 2.6, 8, 6, "#262a30", "#c8d0d8", 2)
p.line(5, 4.3, 8, 4.3, "#c8d0d8", 2)
p.txt(6.5, 3.55, "WC DAMEN", 11, "#e0f0ff", "bold"); p.txt(6.5, 5.25, "WC HERREN", 11, "#e0f0ff", "bold")
for zc in (3.45, 5.15):
	p.door(5, zc, False, 0.9, "#7dff9a")
	p.circ(7.55, zc, 6, "#ddd")
p.rect(6.05, 2.7, 6.55, 3.0, "#ddd"); p.rect(6.05, 5.65, 6.55, 5.95, "#ddd")
# лестница
p.rect(-7.4, 5.0, -1.4, 6.0, "#2b2b36", "#6aa8ff", 2)
for i in range(25):
	x = -7.4 + i * 0.25
	p.line(x, 5.0, x, 6.0, "#4a5a80", 1)
p.line(-7.0, 5.5, -1.9, 5.5, "#9cc4ff", 2, 'marker-end="url(#arr)"')
p.txt(-4.4, 5.38, "ЛЕСТНИЦА ↑ 2 этаж (24 ступени, 6 м)", 10, "#9cc4ff", "bold")
# диван у входа, вход
p.rect(1.7, 5.15, 4.1, 6, "#1d2a4a", "#6aa8ff", 1); p.rect(2.4, 4.4, 3.4, 4.9, DECOR)
p.rect(-0.8, 5.85, 0.8, 6.05, "#ffcc00", "#111", 1)
p.txt(0, 6.45, "ВХОД · ШЛЮЗ", 11, "#7dff9a", "bold")
p.rect(-3.4, -6, 0.2, -5.85, "#6aa8ff"); p.txt(-1.6, -5.55, "вывеска NEON", 9, "#9cc4ff")

# ================================ 2 ЭТАЖ ================================================
p = p2
text_px(p.X(-8), p.Y(-6) - 8, "2 ЭТАЖ (1. OG) · пол 4,3 м, потолок 7,8 м", 15, "#c7b8ff", "bold")
p.grid(-8, -6, 8, 6)
p.rect(-8, -6, 8, 6, "#1d1a22", WALLC, 6)
# проём над сценой (второй свет)
p.rect(1, -6, 8, -1.4, "url(#hatch)", "#6aa8ff", 1.5)
p.txt(4.5, -3.9, "ПРОЁМ НАД СЦЕНОЙ", 12, "#9cc4ff", "bold")
p.txt(4.5, -3.5, "вид на сцену сверху", 10, "#9cc4ff")
p.line(1, -1.4, 5, -1.4, "#bfe0ff", 4); p.line(1, -6, 1, -1.4, "#bfe0ff", 4)
p.txt(3.0, -1.7, "ГАЛЕРЕЯ (ограждение)", 11, "#bfe0ff", "bold")
for x in (1.9, 3.6):
	p.circ(x, -0.85, 0.32 * S, DECOR, "#c9a36a")
# игровая
p.rect(-8, -6, 1, -1.4, "rgba(255,80,180,0.06)", "#ff50b4", 1, 'stroke-dasharray="5 4"')
p.txt(-3.5, -1.75, "ИГРОВАЯ", 13, "#ff9ad5", "bold")
p.rect(-5.5, -4.45, -2.9, -2.95, "#0f3a22", "#c9a36a", 2); p.txt(-4.2, -3.6, "бильярд", 10)
p.rect(-1.28, -5.05, -0.52, -3.75, "#0f3a22", "#c9a36a", 1.5); p.txt(-0.9, -4.4, "кикер", 9, rot=-90)
for x in (-7.2, -6.1):
	p.circ(x, -5.9, 7, "#a01010", "#fff")
p.line(-7.55, -3.61, -5.75, -3.61, "#ffffff", 2)
p.txt(-6.65, -5.45, "дартс", 9)
p.rect(-2.75, -5.95, -1.85, -5.35, "#3a1030", "#ff50b4"); p.txt(-2.3, -5.05, "jukebox", 9)
p.rect(-8, -3.2, -7.85, -2.0, "#20e0c0"); p.txt(-7.6, -1.9, "окно", 8, "#7fffe6", anchor="start")
# лаунж
p.rect(-8, -1.4, -1.6, 4.9, "rgba(106,168,255,0.06)", "#6aa8ff", 1, 'stroke-dasharray="5 4"')
p.txt(-6.6, -1.0, "ЛАУНЖ", 13, "#9cc4ff", "bold")
p.rect(-7.7, -0.6, -3.5, 3.8, "#2a1530")                         # ковёр (декор)
p.rect(-8, 0.7, -7.66, 2.5, "#ff7a20"); p.txt(-7.2, 2.95, "камин", 9, "#ffb070")
p.rect(-4.72, -0.1, -3.88, 2.9, "#1a2a5a", "#6aa8ff"); p.rect(-7.1, 3.33, -4.7, 4.18, "#1a2a5a", "#6aa8ff")
p.rect(-6.5, 1.2, -5.3, 2.0, DECOR, "#c9a36a")
for x, z in [(-6.8, -0.5), (-5.2, -0.6)]:
	p.rect(x - 0.4, z - 0.4, x + 0.4, z + 0.4, "#2a3a5a", "#6aa8ff")
# столики с диванами
p.rect(-1.3, -0.45, 3.65, 3.95, "rgba(201,163,106,0.06)", "#c9a36a", 1, 'stroke-dasharray="5 4"')
p.txt(1.5, 4.35, "СТОЛИКИ И ДИВАНЫ", 12, "#e8d2a8", "bold")
for x, z in [(0.4, 0.6), (2.65, 0.6), (0.4, 2.9), (2.65, 2.9)]:
	p.rect(x - 0.75, z - 0.95, x + 0.75, z - 0.4, "#2a3a5a", "#6aa8ff")
	p.rect(x - 0.65, z - 0.35, x + 0.65, z + 0.35, DECOR, "#c9a36a")
	p.rect(x - 0.75, z + 0.4, x + 0.75, z + 0.95, "#2a3a5a", "#6aa8ff")
# лестница (проём) и площадка
p.rect(-7.4, 5.0, -1.4, 6.0, "url(#hatch)", "#6aa8ff", 1.5)
p.line(-7.4, 5.0, -1.4, 5.0, "#bfe0ff", 4)
p.txt(-4.4, 5.62, "проём лестницы ↓", 10, "#9cc4ff", "bold")
p.rect(-1.4, 4.4, 1.0, 6.0, "rgba(125,255,154,0.08)", "#7dff9a", 1, 'stroke-dasharray="4 3"')
p.txt(-0.2, 4.75, "площадка", 9, "#7dff9a"); p.circ(0.6, 5.6, 5, "#888"); p.txt(0.6, 5.95, "гардероб", 8, "#aaa")
p.rect(0.8, 5.9, 2.2, 6.0, "#20e0c0")
# приватные комнаты
for k, (z0, z1, c) in enumerate([(-1.4, 1.1, "#4070ff"), (1.1, 3.55, "#ff40a0"), (3.55, 6.0, "#ff7030")]):
	p.rect(5, z0, 8, z1, "#2a1220", "#ff8aa8", 2)
	zc = (z0 + z1) / 2
	p.rect(7.08, zc - 0.95, 7.93, zc + 0.95, "#5a1426")
	p.rect(6.2, zc - 0.45, 6.8, zc + 0.45, DECOR)
	p.door(5, zc, False, 0.9, "#ff50b4")
	p.txt(5.75, zc + 0.12, str(k + 1), 18, c, "bold")
	p.rect(7.93, zc - 0.5, 8, zc + 0.5, "#20e0c0")
p.txt(6.5, -1.6, "ПРИВАТНЫЕ КОМНАТЫ", 11, "#ff8aa8", "bold")
p.rect(4, -1.4, 5, 6, "rgba(255,138,168,0.05)", "#ff8aa8", 1, 'stroke-dasharray="3 3"')
p.txt(4.5, 2.3, "коридор", 9, "#ff8aa8", rot=-90)

# ================================ ЛЕГЕНДА ===============================================
lx, ly = p2.X(-8), p2.Y(6) + 34
text_px(lx, ly, "Легенда", 15, weight="bold")
items = [(COLL, "#ffb070", "коллизия из ClubRoom.gd (стойка) — не меняется"), ("#26263a", "#6aa8ff", "сцена (коллизия) / лестница"),
	(DECOR, "#c9a36a", "мебель и техника (новое)"), ("#262a30", "#c8d0d8", "туалеты — на месте прежней кабинки"),
	("#2a1220", "#ff8aa8", "приватные комнаты (кабинка переезжает сюда, ×3)"), ("url(#hatch)", "#6aa8ff", "проём в перекрытии")]
y = ly + 24
for fill, st, lab in items:
	OUT.append(f'<rect x="{lx}" y="{y - 11}" width="22" height="14" fill="{fill}" stroke="{st}" stroke-width="1.5"/>')
	text_px(lx + 32, y, lab, 12); y += 21
OUT.append(f'<line x1="{lx}" y1="{y - 4}" x2="{lx + 22}" y2="{y - 4}" stroke="#7dff9a" stroke-width="4"/>'); text_px(lx + 32, y, "дверь / проём", 12); y += 21
OUT.append(f'<rect x="{lx}" y="{y - 11}" width="22" height="6" fill="#20e0c0"/>'); text_px(lx + 32, y, "заколоченное окно, за ним свечение поля", 12); y += 26
cx = lx + 380
text_px(cx, ly, "Точки игры (1 этаж)", 13, weight="bold")
yy = ly + 22
for k, lab in [("S", "смена бармена"), ("$", "скупка Ankauf"), ("St", "сцена"), ("T", "чаевые"), ("E", "выход на улицу")]:
	OUT.append(f'<circle cx="{cx + 9}" cy="{yy - 4}" r="8" fill="#ffd23f" stroke="#111"/>')
	OUT.append(f'<text x="{cx + 9}" y="{yy}" font-size="9" fill="#111" text-anchor="middle" font-weight="bold" {FONT}>{k}</text>')
	text_px(cx + 24, yy, lab, 12); yy += 20
OUT.append(f'<circle cx="{cx + 9}" cy="{yy - 4}" r="8" fill="#ff50b4" stroke="#fff"/>'); text_px(cx + 24, yy, "W — работница бара (Farah)", 12, "#ff9ad5")

OUT.insert(1, '<defs><pattern id="hatch" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
	'<rect width="8" height="8" fill="#101016"/><line x1="0" y1="0" x2="0" y2="8" stroke="#3a4a70" stroke-width="3"/></pattern>'
	'<marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#9cc4ff"/></marker></defs>')
OUT.append("</svg>")
open("club2_plan.svg", "w").write("\n".join(OUT))
print("ok", TOT_W, TOT_H)
