# Мелкий реквизит клуба «Neon» (раздел C списка ассетов): всё сделано здесь, без загрузок.
# Подключается из build_club2.py (exec, общие функции и переменные). Текстуры — props_tex/ (make_prop_textures.py).
import re

TEX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "props_tex")
IMG_MATS = {}


def img_mat(name, file, rough=0.5, alpha=False, emit=0.0, metal=0.0, clearcoat=0.0):
	key = (name, file)
	if key in IMG_MATS:
		return IMG_MATS[key]
	m = bpy.data.materials.new(name)
	m.use_nodes = True
	nt = m.node_tree
	b = nt.nodes["Principled BSDF"]
	t = nt.nodes.new("ShaderNodeTexImage")
	t.image = bpy.data.images.load(os.path.join(TEX_DIR, file), check_existing=True)
	nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
	if alpha:
		nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
	if emit:
		nt.links.new(t.outputs["Color"], b.inputs["Emission Color"])
		b.inputs["Emission Strength"].default_value = emit
	b.inputs["Roughness"].default_value = rough
	b.inputs["Metallic"].default_value = metal
	if clearcoat:
		b.inputs["Coat Weight"].default_value = clearcoat
	IMG_MATS[key] = m
	return m


class MB:
	"""Сборка одного меша из частей с разными материалами (для экземпляров)."""

	def __init__(self):
		self.bm = bmesh.new()
		self.uv = self.bm.loops.layers.uv.new("UVMap")
		self.mats = []

	def _mi(self, m):
		if m not in self.mats:
			self.mats.append(m)
		return self.mats.index(m)

	def lathe(self, prof, m, segs=32, ox=0.0, oy=0.0, oz=0.0, cap_top=True, cap_bot=True):
		"""prof — [(r, y)] снизу вверх (Godot y). Ось — вертикаль через (ox, oz)."""
		mi = self._mi(m)
		rings = []
		for r, y in prof:
			ring = []
			for k in range(segs):
				a = 2 * math.pi * k / segs
				ring.append(self.bm.verts.new(g2b(ox + r * math.cos(a), oy + y, oz + r * math.sin(a))))
			rings.append(ring)
		for i in range(len(rings) - 1):
			for k in range(segs):
				a, b_ = rings[i][k], rings[i][(k + 1) % segs]
				c, d = rings[i + 1][(k + 1) % segs], rings[i + 1][k]
				try:
					f = self.bm.faces.new((a, d, c, b_))
					f.material_index = mi
					f.smooth = True
				except ValueError:
					pass
		for cap, ring, top in ((cap_bot, rings[0], False), (cap_top, rings[-1], True)):
			if cap and prof[0 if not top else -1][0] > 1e-4:
				try:
					f = self.bm.faces.new(ring if not top else list(reversed(ring)))
					f.material_index = mi
				except ValueError:
					pass

	def band(self, r, y0, y1, m, segs=48, ox=0.0, oy=0.0, oz=0.0, u_center=0.5):
		"""Боковина цилиндра с развёрткой: u = 0..1 по окружности, середина u_center смотрит на +X (Godot)."""
		mi = self._mi(m)
		bot, top = [], []
		for k in range(segs + 1):
			u = k / segs
			a = (u - u_center) * 2 * math.pi
			x, z = ox + r * math.cos(a), oz - r * math.sin(a)
			bot.append((self.bm.verts.new(g2b(x, oy + y0, z)), u))
			top.append((self.bm.verts.new(g2b(x, oy + y1, z)), u))
		for k in range(segs):
			vs = (bot[k][0], bot[k + 1][0], top[k + 1][0], top[k][0])
			uvs = ((bot[k][1], 0), (bot[k + 1][1], 0), (top[k + 1][1], 1), (top[k][1], 1))
			f = self.bm.faces.new(vs)
			f.material_index = mi
			f.smooth = True
			for loop, uv in zip(f.loops, uvs):
				loop[self.uv].uv = uv

	def quad(self, c, w, h, facing, m, uv=((0, 0), (1, 0), (1, 1), (0, 1))):
		"""Прямоугольник с картинкой; facing — '+x', '-x', '+z', '-z', '+y' (куда смотрит лицо)."""
		mi = self._mi(m)
		x, y, z = c
		hw, hh = w / 2, h / 2
		pts = {"+z": [(x - hw, y - hh, z), (x + hw, y - hh, z), (x + hw, y + hh, z), (x - hw, y + hh, z)],
			"-z": [(x + hw, y - hh, z), (x - hw, y - hh, z), (x - hw, y + hh, z), (x + hw, y + hh, z)],
			"+x": [(x, y - hh, z + hw), (x, y - hh, z - hw), (x, y + hh, z - hw), (x, y + hh, z + hw)],
			"-x": [(x, y - hh, z - hw), (x, y - hh, z + hw), (x, y + hh, z + hw), (x, y + hh, z - hw)],
			"+y": [(x - hw, y, z + hh), (x + hw, y, z + hh), (x + hw, y, z - hh), (x - hw, y, z - hh)]}[facing]
		f = self.bm.faces.new([self.bm.verts.new(g2b(*p)) for p in pts])
		f.material_index = mi
		for loop, t in zip(f.loops, uv):
			loop[self.uv].uv = t

	def disc(self, c, r, m, segs=40):
		"""Круг лицом вверх с круговой развёрткой (подставка)."""
		mi = self._mi(m)
		x, y, z = c
		vs, uvs = [], []
		for k in range(segs):
			a = 2 * math.pi * k / segs
			vs.append(self.bm.verts.new(g2b(x + r * math.cos(a), y, z - r * math.sin(a))))
			uvs.append((0.5 + 0.5 * math.cos(a), 0.5 + 0.5 * math.sin(a)))
		f = self.bm.faces.new(vs)
		f.material_index = mi
		for loop, t in zip(f.loops, uvs):
			loop[self.uv].uv = t

	def box(self, c, s, m):
		mi = self._mi(m)
		res = bmesh.ops.create_cube(self.bm, size=1.0)
		for v in res["verts"]:
			v.co = g2b(c[0] + v.co.x * s[0], c[1] + v.co.z * s[1], c[2] - v.co.y * s[2])
		for f in {f for v in res["verts"] for f in v.link_faces}:
			f.material_index = mi

	def mesh(self, name):
		me = bpy.data.meshes.new(name)
		bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
		self.bm.to_mesh(me)
		self.bm.free()
		for m in self.mats:
			me.materials.append(m)
		return me


def inst(name, me, pos, rot_y=0.0):
	"""Экземпляр меша me в точке pos (Godot), поворот вокруг вертикали."""
	o = bpy.data.objects.new(name, me)
	COL.objects.link(o)
	o.location = g2b(*pos)
	o.rotation_euler = (0, 0, rot_y)
	return o


def make(name, build):
	mb = MB()
	build(mb)
	return mb.mesh(name)


# --- материалы реквизита ---------------------------------------------------------------
def glass_mat(name, color, rough=0.02):
	m = mat(name, color, rough, trans=1.0)
	m.node_tree.nodes["Principled BSDF"].inputs["IOR"].default_value = 1.5
	return m


CLEAR = glass_mat("glass_clear", (0.95, 0.97, 0.98))
G_GREEN = glass_mat("glass_green", (0.15, 0.45, 0.2))
G_BROWN = glass_mat("glass_brown", (0.45, 0.22, 0.06))
G_FROST = glass_mat("glass_frost", (0.9, 0.92, 0.95), 0.25)
BEER = mat("beer", (0.85, 0.5, 0.08), 0.05, trans=0.9)
FOAM = mat("foam", (0.95, 0.93, 0.86), 0.6)
L_CLEAR = glass_mat("liquid_clear", (0.92, 0.95, 0.97))
L_AMBER = glass_mat("liquid_amber", (0.6, 0.3, 0.05))
L_DARK = glass_mat("liquid_dark", (0.2, 0.06, 0.02))
L_HERB = glass_mat("liquid_herb", (0.25, 0.12, 0.03))
CAP_GOLD = mat("cap_gold", (0.8, 0.6, 0.25), 0.3, 1.0)
CAP_RED = mat("cap_red", (0.6, 0.05, 0.04), 0.4, 0.6)
CAP_BLACK = mat("cap_black", (0.02, 0.02, 0.02), 0.4)
RED_PAINT = mat("red_paint", (0.55, 0.02, 0.02), 0.25)
KEG = mat("keg_steel", (0.62, 0.63, 0.65), 0.28, 1.0)
CRATE_Y = mat("crate_yellow", (0.75, 0.55, 0.03), 0.5)
CRATE_B = mat("crate_blue", (0.03, 0.12, 0.45), 0.5)
KETCHUP = mat("ketchup", (0.6, 0.03, 0.02), 0.3)
MUSTARD = mat("mustard", (0.75, 0.55, 0.05), 0.4)
CHAIN = mat("chain", (0.3, 0.3, 0.32), 0.4, 1.0)
CABLE = mat("cable", (0.015, 0.015, 0.015), 0.5)

# --- бутылки: профили (r, y) в метрах ----------------------------------------------------
PROFILES = {
	"korn": [(0.0, 0), (0.033, 0), (0.035, 0.006), (0.035, 0.2), (0.031, 0.222), (0.015, 0.255), (0.012, 0.29), (0.012, 0.305), (0.0135, 0.31), (0.0135, 0.322), (0, 0.322)],
	"vodka": [(0.0, 0), (0.038, 0), (0.04, 0.006), (0.04, 0.19), (0.037, 0.215), (0.017, 0.245), (0.0135, 0.27), (0.0135, 0.29), (0.015, 0.295), (0.015, 0.31), (0, 0.31)],
	"kraeuter": [(0.0, 0), (0.044, 0), (0.046, 0.006), (0.046, 0.12), (0.04, 0.142), (0.02, 0.16), (0.014, 0.175), (0.014, 0.19), (0.016, 0.195), (0.016, 0.208), (0, 0.208)],
	"rum": [(0.0, 0), (0.041, 0), (0.043, 0.005), (0.043, 0.17), (0.035, 0.19), (0.017, 0.205), (0.014, 0.23), (0.0155, 0.235), (0.0155, 0.25), (0, 0.25)],
	"gin": [(0.0, 0), (0.044, 0), (0.046, 0.006), (0.046, 0.18), (0.03, 0.2), (0.016, 0.21), (0.014, 0.23), (0.016, 0.235), (0.016, 0.25), (0, 0.25)],
	"whisky": [(0.0, 0), (0.042, 0), (0.044, 0.006), (0.044, 0.19), (0.038, 0.205), (0.016, 0.22), (0.0135, 0.25), (0.016, 0.255), (0.016, 0.275), (0, 0.275)],
	"beer": [(0.0, 0), (0.029, 0), (0.031, 0.006), (0.031, 0.12), (0.027, 0.15), (0.014, 0.185), (0.0125, 0.215), (0.0135, 0.22), (0.0135, 0.226), (0, 0.226)],
}
# тип: (профиль, стекло, жидкость, крышка, этикетка, низ/верх этикетки)
BOTTLES = {
	"korn": ("korn", CLEAR, L_CLEAR, CAP_RED, "label_korn.png", 0.05, 0.16),
	"vodka": ("vodka", G_FROST, L_CLEAR, CAP_BLACK, "label_vodka.png", 0.05, 0.15),
	"kraeuter": ("kraeuter", G_GREEN, L_HERB, CAP_GOLD, "label_kraeuter.png", 0.025, 0.105),
	"rum": ("rum", G_BROWN, L_DARK, CAP_BLACK, "label_rum.png", 0.04, 0.14),
	"gin": ("gin", CLEAR, L_CLEAR, CAP_GOLD, "label_gin.png", 0.04, 0.15),
	"whisky": ("whisky", CLEAR, L_AMBER, CAP_BLACK, "label_whisky.png", 0.04, 0.15),
	"beer": ("beer", G_BROWN, BEER, CAP_GOLD, "label_beer.png", 0.03, 0.095),
}
BOTTLE_MESH = {}
for kind, (pk, gm, lm, cm, lab, ly0, ly1) in BOTTLES.items():
	prof = PROFILES[pk]
	def _b(mb, prof=prof, gm=gm, lm=lm, cm=cm, lab=lab, ly0=ly0, ly1=ly1):
		mb.lathe(prof, gm)
		fill = [(r * 0.9, y) for r, y in prof if y < prof[-1][1] * 0.72 and r > 0.0] or [(0.01, 0.005)]
		mb.lathe([(0, 0.004)] + [(r, max(y, 0.004)) for r, y in fill] + [(0, fill[-1][1])], lm, segs=24)
		top = prof[-1][1]
		neck_r = prof[-3][0]
		mb.lathe([(0, top - 0.018), (neck_r + 0.0012, top - 0.018), (neck_r + 0.0012, top + 0.004), (0, top + 0.004)], cm, segs=24)
		body_r = max(r for r, _ in prof) + 0.0008
		mb.band(body_r, ly0, ly1, img_mat("lab_" + lab, lab, 0.45), segs=48)
	BOTTLE_MESH[kind] = make("bottle_" + kind, _b)

# пивной бокал «тюльпан» с пивом и пеной, «Stange», шот, пепельница, подставка
PILS_PROF = [(0, 0), (0.035, 0), (0.035, 0.008), (0.006, 0.02), (0.005, 0.07), (0.028, 0.1), (0.036, 0.15), (0.033, 0.2), (0.031, 0.215)]


def _pils(mb, full=0.85):
	mb.lathe(PILS_PROF, CLEAR, cap_top=False)
	top = 0.07 + (0.2 - 0.07) * full
	beer = [(0, 0.075), (0.026, 0.1), (0.033, 0.15)]
	beer = [(r, y) for r, y in beer if y < top] + [(0.033, top - 0.02)]
	mb.lathe(beer + [(0, top - 0.02)], BEER, segs=24)
	mb.lathe([(0, top - 0.02), (0.033, top - 0.02), (0.034, top + 0.012), (0.02, top + 0.02), (0, top + 0.022)], FOAM, segs=24)


PILS = make("pils_glass", _pils)
EMPTY_PILS = make("pils_empty", lambda mb: mb.lathe(PILS_PROF, CLEAR, cap_top=False))
SHOT = make("shot_glass", lambda mb: (mb.lathe([(0, 0), (0.022, 0), (0.025, 0.06), (0.024, 0.062)], CLEAR, cap_top=False),
	mb.lathe([(0, 0.012), (0.019, 0.012), (0.021, 0.04), (0, 0.04)], L_CLEAR, segs=20)))
ASHTRAY = make("ashtray", lambda mb: mb.lathe([(0, 0), (0.06, 0), (0.065, 0.035), (0.05, 0.035), (0.045, 0.012), (0, 0.012)], CLEAR))
COASTER_M = img_mat("coaster", "coaster.png", 0.8)
COASTER = make("coaster", lambda mb: (mb.disc((0, 0.002, 0), 0.054, COASTER_M), mb.lathe([(0.054, 0), (0.054, 0.002)], COASTER_M, segs=40, cap_top=False, cap_bot=False)))

# --- 1. задняя стенка бара: настоящие бутылки вместо цилиндров ---------------------------
for o in list(bpy.data.objects):
	if re.match(r"^(Bottle|Neck)\d+_\d+$", o.name) or re.match(r"^Glass\d$", o.name):
		bpy.data.objects.remove(o, do_unlink=True)
group("F1")
ORDER = ["korn", "vodka", "gin", "rum", "whisky", "kraeuter", "korn", "gin", "beer", "rum", "vodka", "kraeuter"]
for i, y in enumerate([1.45, 1.95, 2.45]):
	for k in range(22):
		z = BZ - 2.55 + k * 0.243
		kind = ORDER[(k + i * 5) % len(ORDER)]
		inst("Btl%d_%d" % (i, k), BOTTLE_MESH[kind], (-7.82, y + 0.016, z), rot_y=((k * 37 + i * 11) % 9 - 4) * 0.04)
# на стойке: пиво у стульев, шоты, пепельницы, подставки, бутылки у кассы
for i, z in enumerate([-4.2, -2.0, -0.4, 1.4]):
	inst("BarCoaster%d" % i, COASTER, (BX + 0.4, 1.1, z), rot_y=i * 0.9)
	inst("BarBeer%d" % i, PILS if i != 2 else EMPTY_PILS, (BX + 0.4, 1.102, z))
for i, z in enumerate([-1.95, -1.85, -1.75]):
	inst("BarShot%d" % i, SHOT, (BX + 0.35, 1.1, z))
inst("BarAshtray", ASHTRAY, (BX + 0.38, 1.1, -3.1))
for i, (kind, dz) in enumerate([("korn", 0.0), ("kraeuter", 0.12), ("gin", 0.24)]):
	inst("BarBottle%d" % i, BOTTLE_MESH[kind], (BX - 0.3, 1.1, BZ + 1.9 + dz), rot_y=0.3)
# ряд чистых бокалов на рабочей полке бармена
for i in range(10):
	inst("WellGlass%d" % i, EMPTY_PILS, (BX - 0.42, 0.875, BZ - 3.0 + i * 0.12))

# --- 2. меню-доски: над стойкой (на цепях) и над окном выдачи --------------------------
MENU_BAR = img_mat("menu_bar", "menu_bar.png", 0.85)
MENU_K = img_mat("menu_kitchen", "menu_kitchen.png", 0.85)
board = MB()
board.box((BX, 2.95, 0.58), (0.04, 0.67, 1.3), WOOD)
board.quad((BX + 0.022, 2.95, 0.58), 1.26, 0.63, "+x", MENU_BAR)
board.quad((BX - 0.022, 2.95, 0.58), 1.26, 0.63, "-x", MENU_BAR)
inst("MenuBarBoard", board.mesh("menu_bar_board"), (0, 0, 0))
for dz in (-0.55, 0.55):
	beam("MenuChain%.2f" % dz, (BX, 3.28, 0.58 + dz), (BX, H, 0.58 + dz), 0.006, CHAIN, verts=6)
bk = MB()
bk.box((-4.9, 2.95, -5.98), (1.44, 0.68, 0.03), WOOD)
bk.quad((-4.9, 2.95, -5.96), 1.4, 0.64, "+z", MENU_K)
inst("MenuKitchenBoard", bk.mesh("menu_kitchen_board"), (0, 0, 0))
light("MenuSpot", "SPOT", (-4.9, 3.8, -5.2), 25, (1.0, 0.85, 0.65), 0.05, target=(-4.9, 2.9, -5.98), spot_deg=45)

# --- 3. постеры ----------------------------------------------------------------------
def poster_obj(name, file, c, facing, w=0.6):
	pm = MB()
	pm.quad(c, w, w * 1.414, facing, img_mat("poster_" + file, file, 0.7))
	inst(name, pm.mesh(name), (0, 0, 0))


group("F1")
poster_obj("PosterLastCall", "poster_lastcall.png", (0.62, 1.65, -5.985), "+z", 0.55)
poster_obj("PosterMaske", "poster_maske.png", (4.885, 1.45, 4.3), "-x", 0.5)
group("CUT1")
poster_obj("PosterRock", "poster_rocknight.png", (7.985, 1.7, 1.3), "-x", 0.7)
group("F2")
poster_obj("PosterDerby", "poster_derby.png", (0.2, F2 + 1.6, -5.985), "+z", 0.7)

# --- 4. столики: пиво, подставки, пепельницы -------------------------------------------
group("F1")
for i, (x, z) in enumerate([(-2.6, -3.2), (-2.6, -0.2), (0.4, 1.6)]):
	for j, (dx, dz) in enumerate([(-0.15, 0.1), (0.14, -0.12)]):
		inst("TblCoaster%d_%d" % (i, j), COASTER, (x + dx, 1.1, z + dz), rot_y=j + i)
		inst("TblBeer%d_%d" % (i, j), PILS if (i + j) % 3 else EMPTY_PILS, (x + dx, 1.102, z + dz))
	inst("TblAsh%d" % i, ASHTRAY, (x + 0.12, 1.1, z + 0.18))
group("F2")
for k, (x, z) in enumerate([(0.4, 0.6), (2.65, 0.6), (0.4, 2.9), (2.65, 2.9)]):
	for j, dx in enumerate((-0.35, 0.35)):
		inst("BoothCoaster%d_%d" % (k, j), COASTER, (x + dx, F2 + 0.76, z - 0.12 + j * 0.24), rot_y=j * 2 + k)
		inst("BoothBeer%d_%d" % (k, j), PILS, (x + dx, F2 + 0.762, z - 0.12 + j * 0.24))
	if k % 2 == 0:
		inst("BoothBottle%d" % k, BOTTLE_MESH["beer"], (x + 0.1, F2 + 0.76, z + 0.05))
for i, x in enumerate([1.9, 3.6]):
	inst("GalBeer%d" % i, PILS, (x + 0.08, F2 + 1.102, -0.85))
	inst("GalCoaster%d" % i, COASTER, (x + 0.08, F2 + 1.1, -0.85))
inst("LoungeKorn", BOTTLE_MESH["korn"], (-5.9, F2 + 0.4, 1.4))
for i in range(4):
	inst("LoungeShot%d" % i, SHOT, (-6.1 + i * 0.1, F2 + 0.4, 1.75))

# --- 5. кеги и ящики (кухня), огнетушители, знаки выхода -------------------------------
group("F1")
KEG_PROF = [(0, 0), (0.18, 0), (0.2, 0.02), (0.2, 0.06), (0.195, 0.07), (0.2, 0.08), (0.2, 0.25), (0.195, 0.26), (0.2, 0.27),
	(0.2, 0.52), (0.195, 0.53), (0.2, 0.54), (0.2, 0.58), (0.18, 0.6), (0.05, 0.6), (0.05, 0.63), (0, 0.63)]
KEG_M = make("keg", lambda mb: (mb.lathe(KEG_PROF, KEG), mb.lathe([(0, 0.63), (0.03, 0.63), (0.03, 0.66), (0, 0.66)], BLACK, segs=16)))
for i, z in enumerate([-8.3, -7.85]):
	inst("Keg%d" % i, KEG_M, (-7.7, 0, z))


def _crate(mb, col):
	for side in [((0, 0.15, 0.17), (0.4, 0.3, 0.02)), ((0, 0.15, -0.17), (0.4, 0.3, 0.02)), ((0.19, 0.15, 0), (0.02, 0.3, 0.34)), ((-0.19, 0.15, 0), (0.02, 0.3, 0.34)), ((0, 0.01, 0), (0.4, 0.02, 0.34))]:
		mb.box(side[0], side[1], col)
	for ix in range(4):
		for iz in range(3):
			mb.lathe([(r, y + 0.02) for r, y in PROFILES["beer"]], G_BROWN, segs=12, ox=-0.15 + ix * 0.1, oz=-0.11 + iz * 0.11)


CRATE_YM = make("crate_y", lambda mb: _crate(mb, CRATE_Y))
CRATE_BM = make("crate_b", lambda mb: _crate(mb, CRATE_B))
inst("Crate0", CRATE_YM, (-3.0, 0, -6.8))
inst("Crate1", CRATE_BM, (-3.0, 0.3, -6.8), 0.1)
inst("Crate2", CRATE_YM, (-3.45, 0, -6.8), -0.05)

EXT_PROF = [(0, 0), (0.07, 0), (0.08, 0.02), (0.08, 0.45), (0.07, 0.5), (0.03, 0.53), (0.02, 0.56), (0, 0.56)]
EXT = make("extinguisher", lambda mb: (mb.lathe(EXT_PROF, RED_PAINT), mb.box((0.0, 0.6, 0), (0.12, 0.03, 0.03), BLACK),
	mb.box((0.0, 0.35, 0.085), (0.12, 0.1, 0.002), img_mat("sign_exit_small", "sign_exit.png", 0.5))))
inst("ExtHall", EXT, (-1.15, 0.35, 5.85))
inst("ExtKitchen", EXT, (-1.65, 0.35, -9.75), math.pi)
group("F2")
inst("ExtF2", EXT, (1.25, F2 + 0.35, 5.85))
group("F1")
EXIT_M = img_mat("sign_exit", "sign_exit.png", 0.4, emit=2.5)
es = MB()
es.box((0, 2.75, 5.95), (0.62, 0.32, 0.04), BLACK)
es.quad((0, 2.75, 5.928), 0.58, 0.29, "-z", EXIT_M)
inst("ExitSignHall", es.mesh("exit_sign_hall"), (0, 0, 0))
ek = MB()
ek.quad((-2.45, 2.45, -9.965), 0.5, 0.25, "+z", EXIT_M)
inst("ExitSignKitchen", ek.mesh("exit_sign_kitchen"), (0, 0, 0))
for o in list(bpy.data.objects):
	if o.name in ("KBackExit",):
		bpy.data.objects.remove(o, do_unlink=True)

# --- 6. кухня: сковороды на рейлинге, ножи, соусы, гастроёмкости -----------------------
beam("PanRail", (-5.6, 2.0, -7.9), (-3.6, 2.0, -7.9), 0.012, STEEL)
for i in range(4):
	x = -5.4 + i * 0.5
	beam("PanHook%d" % i, (x, 2.0, -7.9), (x, 1.88, -7.9), 0.004, STEEL, verts=6)
	pan = make("pan%d" % i, lambda mb, r=0.12 + (i % 2) * 0.03: (mb.lathe([(0, 0), (r * 0.8, 0), (r, 0.05), (r - 0.005, 0.05), (r * 0.8 - 0.005, 0.005), (0, 0.005)], DARKSTEEL),
		mb.box((r + 0.09, 0.045, 0), (0.18, 0.012, 0.025), BLACK)))
	o = inst("Pan%d" % i, pan, (x, 1.88, -7.9))
	o.rotation_euler = (0, math.pi / 2, 0)
	o.location = g2b(x, 1.62 - (i % 2) * 0.03, -7.9)
box("KnifeStrip", (-1.545, 1.45, -9.0), (0.02, 0.05, 0.5), BLACK)
for i in range(4):
	box("Knife%d" % i, (-1.56, 1.38, -9.18 + i * 0.12), (0.005, 0.22, 0.03), STEEL)
	box("KnifeH%d" % i, (-1.565, 1.55, -9.18 + i * 0.12), (0.012, 0.11, 0.022), BLACK)
SAUCE = {}
for nm, m in (("ketchup", KETCHUP), ("curry", mat("curry_sauce", (0.55, 0.15, 0.03), 0.3)), ("mustard", MUSTARD)):
	SAUCE[nm] = make("sauce_" + nm, lambda mb, m=m: (mb.lathe([(0, 0), (0.03, 0), (0.032, 0.14), (0.02, 0.17), (0.006, 0.2), (0, 0.2)], m),
		mb.lathe([(0, 0.17), (0.02, 0.17), (0.02, 0.19), (0, 0.19)], mat("cap_white", (0.9, 0.9, 0.9), 0.4), segs=16)))
for i, nm in enumerate(["ketchup", "curry", "mustard"]):
	inst("Sauce%d" % i, SAUCE[nm], (-5.3 + i * 0.08, 1.02, -5.7))
	inst("SauceK%d" % i, SAUCE[nm], (-3.6 + i * 0.08, 0.9, -7.7))
GN = make("gn_pan", lambda mb: (mb.box((0, 0.05, 0), (0.32, 0.1, 0.26), STEEL), mb.box((0, 0.098, 0), (0.29, 0.004, 0.23), FOOD_YEL)))
for i in range(2):
	inst("GN%d" % i, GN, (-4.3 + i * 0.36, 0.9, -8.15))

# --- 7. туалеты: мыло, сушилка, бумага, граффити ---------------------------------------
for k, (zc, sink_z, wall_dz) in enumerate([(3.45, 2.85, 2.73), (5.15, 5.82, 5.95)]):
	s = -1 if k == 0 else 1
	box("Soap%d" % k, (6.65, 1.25, wall_dz - s * 0.05), (0.09, 0.16, 0.08), mat("soap_white", (0.85, 0.85, 0.87), 0.3))
	box("Dryer%d" % k, (5.6, 1.35, wall_dz - s * 0.08), (0.28, 0.24, 0.14), STEEL)
	cyl("Paper%d" % k, (7.85, 0.75, zc + 0.45 * (1 if k == 0 else -1)), 0.06, 0.1, mat("paper", (0.95, 0.95, 0.93), 0.9), axis="Z")
GRAF = img_mat("graffiti", "graffiti_wc.png", 0.6, alpha=True)
gm = MB()
gm.quad((6.55, 1.5, 4.225), 2.6, 1.3, "-z", GRAF)
gm.quad((6.55, 1.5, 4.375), 2.6, 1.3, "+z", GRAF)
inst("Graffiti", gm.mesh("graffiti"), (0, 0, 0))

# --- 8. кабели на сцене -----------------------------------------------------------------
def cable(name, pts, r=0.008):
	cu = bpy.data.curves.new(name, "CURVE")
	cu.dimensions = "3D"
	cu.bevel_depth = r
	cu.bevel_resolution = 2
	sp = cu.splines.new("BEZIER")
	sp.bezier_points.add(len(pts) - 1)
	for bp, p in zip(sp.bezier_points, pts):
		bp.co = g2b(*p)
		bp.handle_left_type = bp.handle_right_type = "AUTO"
	o = bpy.data.objects.new(name, cu)
	COL.objects.link(o)
	o.data.materials.append(CABLE)
	return o


group("F1")
cable("CableSpkL", [(1.4, 0.62, -5.0), (2.0, 0.61, -4.6), (3.5, 0.61, -4.5), (4.6, 0.61, -4.6)])
cable("CableSpkR", [(6.6, 0.62, -5.0), (6.3, 0.61, -4.2), (6.2, 0.61, -4.6)])
cable("CableMic", [(3.0, 0.62, -2.0), (3.4, 0.61, -2.6), (4.2, 0.61, -3.1), (4.8, 0.61, -4.3)], 0.005)

# --- 9. износ: тёмные пятна и потёртости на полу ----------------------------------------
fl = bpy.data.materials.get("floor_concrete")
if fl:
	nt = fl.node_tree
	b = nt.nodes["Principled BSDF"]
	base = b.inputs["Base Color"].links[0].from_socket
	nz = nt.nodes.new("ShaderNodeTexNoise")
	nz.inputs["Scale"].default_value = 0.35
	nz.inputs["Detail"].default_value = 6
	rmp = nt.nodes.new("ShaderNodeMapRange")
	rmp.inputs["From Min"].default_value = 0.45
	rmp.inputs["From Max"].default_value = 0.7
	rmp.inputs["To Min"].default_value = 1.0
	rmp.inputs["To Max"].default_value = 0.55
	nt.links.new(nz.outputs["Fac"], rmp.inputs[0])
	mix = nt.nodes.new("ShaderNodeMix")
	mix.data_type = "RGBA"
	mix.blend_type = "MULTIPLY"
	mix.inputs["Factor"].default_value = 1.0
	nt.links.new(base, mix.inputs[6])
	comb = nt.nodes.new("ShaderNodeCombineColor")
	for i in range(3):
		nt.links.new(rmp.outputs[0], comb.inputs[i])
	nt.links.new(comb.outputs[0], mix.inputs[7])
	nt.links.new(mix.outputs[2], b.inputs["Base Color"])
	scr = nt.nodes.new("ShaderNodeTexWave")          # царапины
	scr.inputs["Scale"].default_value = 40
	scr.inputs["Distortion"].default_value = 20
	scr.inputs["Detail"].default_value = 4
	bump = nt.nodes.new("ShaderNodeBump")
	bump.inputs["Strength"].default_value = 0.08
	nt.links.new(scr.outputs["Fac"], bump.inputs["Height"])
	nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
group("F1")
