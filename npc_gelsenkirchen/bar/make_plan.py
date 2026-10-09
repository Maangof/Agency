# Схема бара «Neon Bar» в масштабе по scenes/club/ClubRoom.gd. python3 make_plan.py -> bar_plan.svg
S, M, LW = 52, 60, 330          # px/м, поле, ширина легенды
W, D = 16, 12
def X(x): return M + (x + 8) * S
def Y(z): return M + (z + 6) * S
out = []
def rect(x0, z0, x1, z1, fill, stroke="none", sw=1, extra=""):
	out.append(f'<rect x="{X(min(x0,x1)):.1f}" y="{Y(min(z0,z1)):.1f}" width="{abs(x1-x0)*S:.1f}" height="{abs(z1-z0)*S:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')
def circ(x, z, r, fill, stroke="none", sw=1, extra=""):
	out.append(f'<circle cx="{X(x):.1f}" cy="{Y(z):.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')
def txt(x, z, s, size=12, fill="#e8e8f0", anchor="middle", weight="normal", px=False):
	xx, yy = (x, z) if px else (X(x), Y(z))
	out.append(f'<text x="{xx:.1f}" y="{yy:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" font-family="Arial, sans-serif">{s}</text>')
def spot(x, z, label, color="#ffd23f"):
	circ(x, z, 9, color, "#111", 1.5)
	txt(x, z + 0.09, label, 10, "#111", weight="bold")

COLL, DECOR, WALL = "#5a3a22", "#3a3f55", "#2a2a33"
TOT_W, TOT_H = M * 2 + W * S + LW, M * 2 + D * S + 40
out.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {TOT_W} {TOT_H}" width="{TOT_W}" height="{TOT_H}">')
out.append(f'<rect width="100%" height="100%" fill="#14141a"/>')
txt(M, 34, "NEON BAR (16+) — схема зала, вид сверху. 1 клетка = 1 м", 18, anchor="start", weight="bold", px=True)
# сетка
for i in range(W + 1):
	out.append(f'<line x1="{X(i-8)}" y1="{Y(-6)}" x2="{X(i-8)}" y2="{Y(6)}" stroke="#22222c" stroke-width="1"/>')
for j in range(D + 1):
	out.append(f'<line x1="{X(-8)}" y1="{Y(j-6)}" x2="{X(8)}" y2="{Y(j-6)}" stroke="#22222c" stroke-width="1"/>')
rect(-8, -6, 8, 6, "#1c1c24", "#8888a0", 6)
# сцена (коллизия)
rect(1, -5.8, 7, -1.4, "#26263a", "#6aa8ff", 2)
txt(4, -3.9, "СЦЕНА  h 0,6 м", 14, "#9cc4ff", weight="bold")
txt(4, -3.5, "коллизия StageFloor 6 × 4,4", 11, "#9cc4ff")
rect(4.6, -4.9, 6.2, -4.3, DECOR); txt(5.4, -4.5, "пульт", 10)
rect(1.1, -5.8, 1.7, -5.3, DECOR); rect(6.3, -5.8, 6.9, -5.3, DECOR); txt(4, -5.45, "колонки · ферма с прожекторами", 10, "#aaa")
rect(0.7, -2.55, 1.0, -1.65, DECOR); txt(0.55, -1.9, "ступени", 9, "#aaa", anchor="end")
# стойка (коллизия) и зона работницы
rect(-8, -4.4, -7.57, 2.0, DECOR, "#c9a36a", 1)

rect(-6.7, -4.7, -5.7, 2.3, COLL, "#ffb070", 2)
out.append(f'<text transform="translate({X(-6.2)+5},{Y(-1.2)}) rotate(-90)" font-size="13" fill="#ffd9b0" text-anchor="middle" font-weight="bold" font-family="Arial">СТОЙКА 7 × 1 м, h 1,1</text>')
rect(-7.57, -4.7, -6.7, 2.3, "rgba(255,80,180,0.13)", "#ff50b4", 1.5, 'stroke-dasharray="6 4"')
# работница
circ(-7.25, -1.2, 14, "#ff50b4", "#fff", 2)
out.append(f'<line x1="{X(-7.25)}" y1="{Y(-1.2)}" x2="{X(-6.75)}" y2="{Y(-1.2)}" stroke="#fff" stroke-width="3"/>')
txt(-7.25, -0.75, "W", 12, "#fff", weight="bold")
# якоря анимаций работницы
anchors = [("A1", -7.25, -1.2, "пивные краны"), ("A2", -7.25, 1.25, "касса / кофемашина"), ("A3", -7.25, -2.8, "мойка, стаканы"),
	("A4", -7.25, 1.85, "холодильник"), ("A5", -7.25, 0.5, "приём скупки"), ("A6", -7.2, -5.4, "служебная дверь")]
for a, x, z, _ in anchors[1:]:
	circ(x, z, 10, "#2a1426", "#ff50b4", 2)
	txt(x, z + 0.07, a, 9, "#ff9ad5", weight="bold")
txt(-7.25, -1.55, "A1", 10, "#ff9ad5", weight="bold")
rect(-7.65, -6, -6.75, -5.9, "#888"); txt(-7.2, -5.65, "PERSONAL", 9, "#ccc")
# стулья
for z in [-4.2, -2.0, -1.2, -0.4, 1.4, 2.0]:
	circ(-5.25, z, 9, "#2a4a8a", "#6aa8ff", 1)
# точки игры
spot(-4.9, -3.0, "S"); spot(-4.9, 0.5, "$")
spot(4.0, -0.4, "St"); spot(7.2, -0.4, "T")
spot(0, 5.6, "E"); circ(0, 4.2, 6, "#4cff7a")
spot(4.6, 4.2, "Bi"); spot(6.5, 3.3, "Bo")
rect(7.0, -1.2, 7.4, -0.8, DECOR)
# кабинка
rect(4.9, 2.6, 5.1, 6, COLL, "#ffb070", 1); rect(4.9, 2.5, 8, 2.7, COLL, "#ffb070", 1)
rect(5.1, 2.7, 8, 6, "rgba(160,20,60,0.25)")
rect(7.15, 3.2, 8, 5.8, "#5a1426"); txt(7.6, 4.5, "диван", 10)
txt(6.3, 5.6, "КАБИНКА", 13, "#ff8aa8", weight="bold")
rect(4.85, 3.7, 4.92, 4.7, "#a0143c")
# вход
rect(-0.8, 5.85, 0.8, 6.05, "#ffcc00", "#111", 1); txt(0, 6.45, "ВХОД · ШЛЮЗ (SCHLEUSE)", 12, "#7dff9a", weight="bold")
rect(-0.8, 4.2, 0.8, 5.6, "none", "#ffcc00", 1.5, 'stroke-dasharray="4 4"')
# столики и диваны
for x, z in [(-2.6, -3.2), (-2.6, -0.2), (0.4, 1.6)]:
	circ(x, z, 0.38 * S, DECOR, "#c9a36a", 1)
for x in [-6.6, -4.4]:
	rect(x - 1, 5.15, x + 1, 6, "#1d2a4a", "#6aa8ff", 1); rect(x - 0.45, 4.45, x + 0.45, 4.95, DECOR)
txt(-5.5, 5.75, "диваны (лаунж-угол)", 10, "#9cc4ff")
# вывеска
rect(-3.4, -6, 0.2, -5.85, "#6aa8ff"); txt(-1.6, -5.55, "вывеска NEON · BLAU-WEISS 04", 11, "#9cc4ff")
txt(4, -5.95 + 0.0, "", 1)
# компас
out.append(f'<text x="{X(8)-14}" y="{Y(-6)+22}" font-size="14" fill="#888" font-family="Arial">N↑</text>')
# легенда
lx = M * 2 + W * S - 20
ly = M + 10
def leg(y, sw, label, kind="rect", color="#fff", text_color="#e8e8f0"):
	if kind == "rect":
		out.append(f'<rect x="{lx}" y="{y-11}" width="22" height="14" fill="{sw}" stroke="{color}" stroke-width="1.5"/>')
	else:
		out.append(f'<circle cx="{lx+11}" cy="{y-4}" r="8" fill="{sw}" stroke="#111"/>')
		out.append(f'<text x="{lx+11}" y="{y}" font-size="9" fill="#111" text-anchor="middle" font-weight="bold" font-family="Arial">{color}</text>')
	out.append(f'<text x="{lx+32}" y="{y}" font-size="12" fill="{text_color}" font-family="Arial">{label}</text>')
txt(lx, ly, "Легенда", 15, anchor="start", weight="bold", px=True)
y = ly + 26
for sw, c, lab in [(COLL, "#ffb070", "коллизия игры (не меняется)"), ("#26263a", "#6aa8ff", "сцена (коллизия)"), (DECOR, "#c9a36a", "декор — предложение"),
		("rgba(255,80,180,0.13)", "#ff50b4", "зона работницы, проход 0,87 м"), (DECOR, "#c9a36a", "у западной стены — задняя стенка бара")]:
	leg(y, sw, lab, color=c); y += 22
y += 6
txt(lx, y, "Точки игры (ClubSpot / ShopCounter)", 13, anchor="start", weight="bold", px=True); y += 22
for k, lab in [("S", "смена бармена (−4,9; −3,0)"), ("$", "скупка Ankauf (−4,9; 0,5)"), ("St", "сцена (4,0; −0,4)"), ("T", "чаевые (7,2; −0,4)"),
		("Bi", "вход в кабинку"), ("Bo", "выход из кабинки"), ("E", "выход на улицу; ● вход (0; 4,2)")]:
	leg(y, "#ffd23f", lab, kind="spot", color=k); y += 21
y += 8
txt(lx, y, "Работница W (−7,25; −1,2), лицом на +X", 13, anchor="start", weight="bold", px=True, fill="#ff9ad5"); y += 20
txt(lx, y, "Якоря анимаций (только вид, без сети):", 12, anchor="start", px=True); y += 18
for a, x, z, lab in anchors:
	txt(lx + 6, y, f"{a} — {lab}", 12, "#ff9ad5", anchor="start", px=True); y += 17
y += 8
for line in ["Все стулья — между точками S и $,", "к точкам свободный подход ≥ 0,7 м.", "Столики, диваны, пульт — новые",
		"коллизии: нужен --nav-check.", "Размер зала 16 × 12 × 4 м (SIZE)."]:
	txt(lx, y, line, 11, "#aaa", anchor="start", px=True); y += 16
out.append("</svg>")
open("bar_plan.svg", "w").write("\n".join(out))
print("ok", TOT_W, TOT_H)
