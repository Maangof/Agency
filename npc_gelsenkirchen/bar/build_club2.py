# Клуб «Neon» в 2 этажа (16+): 1 этаж — бар, сцена, 2 туалета, кухня за дверью у бара;
# 2 этаж — лаунж, 3 приватные комнаты, столики и диваны, галерея над сценой, игровая (кикер, бильярд, дартс).
# Основа — scenes/club/ClubRoom.gd (зал 16 × 12, стойка и сцена — те же коллизии).
# Запуск: python build_club2.py <папка вывода> [--quick] [--only=имя]   (Blender как модуль bpy)
#     или: blender -b -P build_club2.py -- <папка вывода> [--quick]
# Координаты в коде — как в Godot (x вправо, y вверх, -z север); в Blender: (x, -z, y).
# Коллизии игры (стойка, сцена, стены кабинки) не меняются — всё остальное декор.
import bpy, bmesh, math, sys, os
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
OUT = argv[0] if argv else "."
QUICK = "--quick" in argv
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
COL = sc.collection
CEILING = []   # скрыть на виде сверху


def g2b(x, y, z):
	return Vector((x, -z, y))


# --- материалы -------------------------------------------------------------------------
MATS = {}


def mat(name, color=(0.5, 0.5, 0.5), rough=0.5, metal=0.0, emit=None, strength=0.0, trans=0.0, sheen=0.0):
	if name in MATS:
		return MATS[name]
	m = bpy.data.materials.new(name)
	m.use_nodes = True
	b = m.node_tree.nodes["Principled BSDF"]
	b.inputs["Base Color"].default_value = (*color, 1)
	b.inputs["Roughness"].default_value = rough
	b.inputs["Metallic"].default_value = metal
	if emit:
		b.inputs["Emission Color"].default_value = (*emit, 1)
		b.inputs["Emission Strength"].default_value = strength
	if trans:
		b.inputs["Transmission Weight"].default_value = trans
	if sheen:
		b.inputs["Sheen Weight"].default_value = sheen
	MATS[name] = m
	return m


def brick_mat(name, axes, c1=(0.22, 0.07, 0.045), c2=(0.13, 0.05, 0.04), mortar=(0.05, 0.05, 0.05), bw=0.25, rh=0.075, rough=0.85):
	"""Кирпич по мировым координатам; axes — пара осей Blender для плоскости стены."""
	m = bpy.data.materials.new(name)
	m.use_nodes = True
	nt = m.node_tree
	b = nt.nodes["Principled BSDF"]
	geo = nt.nodes.new("ShaderNodeNewGeometry")
	sep = nt.nodes.new("ShaderNodeSeparateXYZ")
	comb = nt.nodes.new("ShaderNodeCombineXYZ")
	nt.links.new(geo.outputs["Position"], sep.inputs[0])
	nt.links.new(sep.outputs[axes[0]], comb.inputs[0])
	nt.links.new(sep.outputs[axes[1]], comb.inputs[1])
	br = nt.nodes.new("ShaderNodeTexBrick")
	br.inputs["Color1"].default_value = (*c1, 1)
	br.inputs["Color2"].default_value = (*c2, 1)
	br.inputs["Mortar"].default_value = (*mortar, 1)
	br.inputs["Scale"].default_value = 1.0
	br.inputs["Mortar Size"].default_value = 0.012
	br.inputs["Brick Width"].default_value = bw
	br.inputs["Row Height"].default_value = rh
	nt.links.new(comb.outputs[0], br.inputs["Vector"])
	nz = nt.nodes.new("ShaderNodeTexNoise")
	nz.inputs["Scale"].default_value = 6
	mix = nt.nodes.new("ShaderNodeMix")
	mix.data_type = "RGBA"
	mix.inputs["Factor"].default_value = 1.0
	nt.links.new(br.outputs["Color"], mix.inputs[6])
	mix.blend_type = "MULTIPLY"
	mix.inputs[7].default_value = (1, 1, 1, 1)
	nzr = nt.nodes.new("ShaderNodeMapRange")
	nzr.inputs["To Min"].default_value = 0.6
	nt.links.new(nz.outputs["Fac"], nzr.inputs[0])
	nt.links.new(nzr.outputs[0], mix.inputs[7])
	nt.links.new(mix.outputs[2], b.inputs["Base Color"])
	bump = nt.nodes.new("ShaderNodeBump")
	bump.inputs["Strength"].default_value = 0.4
	nt.links.new(br.outputs["Fac"], bump.inputs["Height"])
	nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
	b.inputs["Roughness"].default_value = rough
	return m


def stripes_mat(name, c1=(0.9, 0.65, 0.02), c2=(0.02, 0.02, 0.02)):
	m = bpy.data.materials.new(name)
	m.use_nodes = True
	nt = m.node_tree
	b = nt.nodes["Principled BSDF"]
	geo = nt.nodes.new("ShaderNodeNewGeometry")
	w = nt.nodes.new("ShaderNodeTexWave")
	w.bands_direction = "DIAGONAL"
	w.inputs["Scale"].default_value = 3.0
	w.inputs["Distortion"].default_value = 0
	nt.links.new(geo.outputs["Position"], w.inputs["Vector"])
	ramp = nt.nodes.new("ShaderNodeValToRGB")
	ramp.color_ramp.interpolation = "CONSTANT"
	ramp.color_ramp.elements[0].color = (*c2, 1)
	ramp.color_ramp.elements[1].position = 0.5
	ramp.color_ramp.elements[1].color = (*c1, 1)
	nt.links.new(w.outputs["Fac"], ramp.inputs[0])
	nt.links.new(ramp.outputs[0], b.inputs["Base Color"])
	b.inputs["Roughness"].default_value = 0.6
	return m


def concrete_mat():
	m = bpy.data.materials.new("floor_concrete")
	m.use_nodes = True
	nt = m.node_tree
	b = nt.nodes["Principled BSDF"]
	nz = nt.nodes.new("ShaderNodeTexNoise")
	nz.inputs["Scale"].default_value = 3
	nz.inputs["Detail"].default_value = 8
	ramp = nt.nodes.new("ShaderNodeValToRGB")
	ramp.color_ramp.elements[0].color = (0.035, 0.035, 0.04, 1)
	ramp.color_ramp.elements[1].color = (0.11, 0.105, 0.11, 1)
	nt.links.new(nz.outputs["Fac"], ramp.inputs[0])
	nt.links.new(ramp.outputs[0], b.inputs["Base Color"])
	r2 = nt.nodes.new("ShaderNodeMapRange")
	r2.inputs["To Min"].default_value = 0.18
	r2.inputs["To Max"].default_value = 0.5
	nt.links.new(nz.outputs["Fac"], r2.inputs[0])
	nt.links.new(r2.outputs[0], b.inputs["Roughness"])
	return m


def wood_mat():
	m = bpy.data.materials.new("wood_dark")
	m.use_nodes = True
	nt = m.node_tree
	b = nt.nodes["Principled BSDF"]
	geo = nt.nodes.new("ShaderNodeNewGeometry")
	mp = nt.nodes.new("ShaderNodeMapping")
	mp.inputs["Scale"].default_value = (1, 1, 14)
	nt.links.new(geo.outputs["Position"], mp.inputs[0])
	nz = nt.nodes.new("ShaderNodeTexWave")
	nz.wave_type = "RINGS"
	nz.inputs["Scale"].default_value = 2
	nz.inputs["Distortion"].default_value = 6
	nt.links.new(mp.outputs[0], nz.inputs["Vector"])
	ramp = nt.nodes.new("ShaderNodeValToRGB")
	ramp.color_ramp.elements[0].color = (0.05, 0.022, 0.01, 1)
	ramp.color_ramp.elements[1].color = (0.16, 0.075, 0.03, 1)
	nt.links.new(nz.outputs["Fac"], ramp.inputs[0])
	nt.links.new(ramp.outputs[0], b.inputs["Base Color"])
	b.inputs["Roughness"].default_value = 0.35
	return m


BRICK_NS = brick_mat("brick_ns", (0, 2))
BRICK_EW = brick_mat("brick_ew", (1, 2))
STRIPES = stripes_mat("stripes")
FLOOR = concrete_mat()
WOOD = wood_mat()
STEEL = mat("steel", (0.55, 0.56, 0.58), 0.32, 1.0)
DARKSTEEL = mat("steel_dark", (0.08, 0.08, 0.09), 0.45, 0.9)
BLACK = mat("black_matte", (0.015, 0.015, 0.018), 0.7)
CEIL = mat("ceiling", (0.03, 0.03, 0.035), 0.9)
NEON_B = mat("neon_blue", (0.1, 0.4, 1), 0.3, emit=(0.15, 0.45, 1.0), strength=18)
NEON_W = mat("neon_white", (1, 1, 1), 0.3, emit=(0.85, 0.92, 1.0), strength=14)
NEON_M = mat("neon_magenta", (1, 0.1, 0.6), 0.3, emit=(1.0, 0.15, 0.55), strength=12)
NEON_M_SOFT = mat("neon_magenta_soft", (0.3, 0.02, 0.15), 0.3, emit=(1.0, 0.15, 0.55), strength=2.5)
WARM = mat("warm_strip", (1, 0.6, 0.3), 0.3, emit=(1.0, 0.55, 0.22), strength=10)
BULB = mat("bulb", (1, 0.8, 0.5), 0.3, emit=(1.0, 0.7, 0.35), strength=25)
GREEN = mat("lamp_green", (0.1, 1, 0.3), 0.3, emit=(0.1, 1.0, 0.25), strength=15)
RED_LAMP = mat("lamp_red", (1, 0.1, 0.05), 0.3, emit=(1.0, 0.08, 0.04), strength=12)
MIRROR = mat("mirror", (0.9, 0.9, 0.95), 0.04, 1.0)
VELVET = mat("velvet", (0.25, 0.02, 0.05), 0.8, sheen=1.0)
LEATHER = mat("leather_blue", (0.02, 0.05, 0.14), 0.45)
BOOTH = mat("booth_wall", (0.12, 0.03, 0.06), 0.6)
STAGE = mat("stage_floor", (0.02, 0.02, 0.03), 0.25)
BOTTLE = [mat("glass_%d" % i, c, 0.06, trans=0.85) for i, c in enumerate(
	[(0.1, 0.35, 0.08), (0.45, 0.2, 0.04), (0.8, 0.8, 0.85), (0.05, 0.15, 0.5), (0.5, 0.05, 0.05)])]
MANNEQUIN = mat("mannequin", (0.45, 0.45, 0.47), 0.6)


# --- примитивы -------------------------------------------------------------------------
def _obj(name, mesh, m):
	o = bpy.data.objects.new(name, mesh)
	COL.objects.link(o)
	if m:
		o.data.materials.append(m)
	return o


def box(name, c, s, m, ceiling=False):
	"""c — центр, s — размер (Godot)."""
	me = bpy.data.meshes.new(name)
	bm = bmesh.new()
	bmesh.ops.create_cube(bm, size=1.0)
	for v in bm.verts:
		v.co = Vector((v.co.x * s[0], v.co.y * s[2], v.co.z * s[1]))
	bm.to_mesh(me)
	bm.free()
	o = _obj(name, me, m)
	o.location = g2b(*c)
	if ceiling:
		CEILING.append(o)
	return o


def cyl(name, c, r, h, m, verts=24, axis="Y", r2=None, ceiling=False):
	me = bpy.data.meshes.new(name)
	bm = bmesh.new()
	bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=r, radius2=r if r2 is None else r2, depth=h)
	bm.to_mesh(me)
	bm.free()
	o = _obj(name, me, m)
	o.location = g2b(*c)
	if axis == "X":
		o.rotation_euler = (0, math.pi / 2, 0)
	elif axis == "Z":
		o.rotation_euler = (math.pi / 2, 0, 0)
	if ceiling:
		CEILING.append(o)
	for p in o.data.polygons:
		p.use_smooth = True
	return o


def sphere(name, c, r, m, ceiling=False):
	me = bpy.data.meshes.new(name)
	bm = bmesh.new()
	bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=r)
	bm.to_mesh(me)
	bm.free()
	o = _obj(name, me, m)
	o.location = g2b(*c)
	for p in o.data.polygons:
		p.use_smooth = True
	if ceiling:
		CEILING.append(o)
	return o


def text(name, body, c, size, m, rot_y=0.0, extrude=0.01):
	"""rot_y — поворот вокруг вертикали (Godot): 0 — текст смотрит на +Z (юг), pi/2 — на +X (восток)."""
	cu = bpy.data.curves.new(name, "FONT")
	cu.body = body
	cu.size = size
	cu.align_x = "CENTER"
	cu.align_y = "CENTER"
	cu.extrude = extrude
	o = bpy.data.objects.new(name, cu)
	COL.objects.link(o)
	o.data.materials.append(m)
	o.location = g2b(*c)
	o.rotation_euler = (math.pi / 2, 0, rot_y)
	return o


def light(name, kind, c, energy, color=(1, 1, 1), size=0.5, target=None, spot_deg=40):
	ld = bpy.data.lights.new(name, kind)
	ld.energy = energy
	ld.color = color
	if kind == "AREA":
		ld.size = size
	elif kind in ("POINT", "SPOT"):
		ld.shadow_soft_size = size
	if kind == "SPOT":
		ld.spot_size = math.radians(spot_deg)
		ld.spot_blend = 0.4
	o = bpy.data.objects.new(name, ld)
	COL.objects.link(o)
	o.location = g2b(*c)
	if target is not None:
		d = g2b(*target) - o.location
		o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
	return o


# ======================================================================================
# Клуб в 2 этажа. Координаты — Godot: x восток, y вверх, -z север. Зал 16 × 12 (x ±8, z ±6).
# 1 этаж: пол 0, потолок (низ перекрытия) 4.0. Перекрытие 4.0..4.3. 2 этаж: пол 4.3, потолок 7.8.
# Кухня — пристройка к северу: x -8..-1.5, z -10..-6, один этаж.
# ======================================================================================
ONLY = next((a.split("=", 1)[1] for a in argv if a.startswith("--only=")), "")
W, D = 16.0, 12.0
hx, hz = W / 2, D / 2
H = 4.0          # низ перекрытия (как высота зала в ClubRoom.SIZE)
F2 = 4.3         # пол 2 этажа
TOP = 7.8        # потолок 2 этажа
COLS = {}


def group(n):
	"""Все следующие объекты — в коллекцию n (для видов с разрезом)."""
	global COL
	if n not in COLS:
		c = bpy.data.collections.new(n)
		sc.collection.children.link(c)
		COLS[n] = c
	COL = COLS[n]


def beam(name, p0, p1, r, m, verts=10):
	"""Цилиндр между точками p0 и p1 (Godot)."""
	a, b = g2b(*p0), g2b(*p1)
	o = cyl(name, (0, 0, 0), r, (b - a).length, m, verts=verts)
	o.location = (a + b) / 2
	o.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()
	return o


def wall_x(name, z, x0, x1, y0, y1, t, m):
	"""Стена вдоль оси x на линии z, толщина t."""
	return box(name, ((x0 + x1) / 2, (y0 + y1) / 2, z), (x1 - x0, y1 - y0, t), m)


def wall_z(name, x, z0, z1, y0, y1, t, m):
	return box(name, (x, (y0 + y1) / 2, (z0 + z1) / 2), (t, y1 - y0, z1 - z0), m)


def wall_holes_x(name, z, x0, x1, y0, y1, t, m, holes):
	"""Стена вдоль x с проёмами holes = [(xa, xb, ya, yb)]."""
	cur = x0
	for i, (xa, xb, ya, yb) in enumerate(sorted(holes)):
		if xa > cur:
			wall_x("%s_%d" % (name, i), z, cur, xa, y0, y1, t, m)
		if ya > y0:
			wall_x("%s_%db" % (name, i), z, xa, xb, y0, ya, t, m)
		if yb < y1:
			wall_x("%s_%dt" % (name, i), z, xa, xb, yb, y1, t, m)
		cur = xb
	if cur < x1:
		wall_x("%s_end" % name, z, cur, x1, y0, y1, t, m)


def wall_holes_z(name, x, z0, z1, y0, y1, t, m, holes):
	cur = z0
	for i, (za, zb, ya, yb) in enumerate(sorted(holes)):
		if za > cur:
			wall_z("%s_%d" % (name, i), x, cur, za, y0, y1, t, m)
		if ya > y0:
			wall_z("%s_%db" % (name, i), x, za, zb, y0, ya, t, m)
		if yb < y1:
			wall_z("%s_%dt" % (name, i), x, za, zb, yb, y1, t, m)
		cur = zb
	if cur < z1:
		wall_z("%s_end" % name, x, cur, z1, y0, y1, t, m)


def railing(name, p0, p1, y0, glass=True):
	"""Ограждение: стойки через ~1 м, поручень 1.05 м, стеклянные панели."""
	a, b = Vector(p0), Vector(p1)   # (x, z)
	n = max(1, int(round((b - a).length)))
	for i in range(n + 1):
		p = a + (b - a) * (i / n)
		cyl("%sPost%d" % (name, i), (p.x, y0 + 0.52, p.y), 0.025, 1.05, STEEL, verts=8)
	beam(name + "Rail", (a.x, y0 + 1.05, a.y), (b.x, y0 + 1.05, b.y), 0.03, STEEL)
	if glass:
		c = (a + b) / 2
		sx = abs(b.x - a.x) or 0.02
		sz = abs(b.y - a.y) or 0.02
		box(name + "Glass", (c.x, y0 + 0.5, c.y), (sx, 0.9, sz), GLASS_RAIL)
		box(name + "LED", (c.x, y0 + 0.02, c.y), (sx, 0.02, sz), NEON_B)


def boarded_window(name, x, y, z, w, h, axis, m_glow):
	"""Заколоченное окно, за досками — свечение защитного поля (лор «Карантин»). axis — 'x' (стена вдоль x) или 'z'."""
	d = 0.03
	if axis == "x":
		box(name + "Glow", (x, y, z), (w, h, 0.02), m_glow)
		box(name + "FrameT", (x, y + h / 2, z + d), (w + 0.12, 0.08, 0.06), DARKSTEEL)
		box(name + "FrameB", (x, y - h / 2, z + d), (w + 0.12, 0.08, 0.06), DARKSTEEL)
		for k in range(4):
			box("%sPlank%d" % (name, k), (x, y - h / 2 + 0.15 + k * (h - 0.3) / 3, z + 2 * d), (w + 0.2, 0.16, 0.03), PLANK)
	else:
		box(name + "Glow", (x, y, z), (0.02, h, w), m_glow)
		box(name + "FrameT", (x + d, y + h / 2, z), (0.06, 0.08, w + 0.12), DARKSTEEL)
		box(name + "FrameB", (x + d, y - h / 2, z), (0.06, 0.08, w + 0.12), DARKSTEEL)
		for k in range(4):
			box("%sPlank%d" % (name, k), (x + 2 * d, y - h / 2 + 0.15 + k * (h - 0.3) / 3, z), (0.03, 0.16, w + 0.2), PLANK)


def sofa(name, c, length, along, back_dir, m, h_seat=0.42, depth=0.85):
	"""Диван: along — 'x'|'z' (длина), back_dir — +1/-1: спинка в сторону +/− перпендикулярной оси."""
	x, y, z = c
	if along == "x":
		box(name, (x, y + h_seat / 2, z), (length, h_seat, depth), m)
		box(name + "Back", (x, y + 0.65, z + back_dir * (depth / 2 - 0.1)), (length, 0.75, 0.2), m)
		box(name + "ArmA", (x - length / 2 + 0.1, y + 0.32, z), (0.2, 0.64, depth), m)
		box(name + "ArmB", (x + length / 2 - 0.1, y + 0.32, z), (0.2, 0.64, depth), m)
	else:
		box(name, (x, y + h_seat / 2, z), (depth, h_seat, length), m)
		box(name + "Back", (x + back_dir * (depth / 2 - 0.1), y + 0.65, z), (0.2, 0.75, length), m)
		box(name + "ArmA", (x, y + 0.32, z - length / 2 + 0.1), (depth, 0.64, 0.2), m)
		box(name + "ArmB", (x, y + 0.32, z + length / 2 - 0.1), (depth, 0.64, 0.2), m)


def pendant(name, x, z, ceil_y, drop, m_shade=None, energy=45, color=(1.0, 0.72, 0.45)):
	cyl(name + "Cord", (x, ceil_y - drop / 2, z), 0.006, drop, BLACK, verts=6)
	cyl(name + "Shade", (x, ceil_y - drop - 0.08, z), 0.2, 0.18, m_shade or DARKSTEEL, r2=0.05)
	sphere(name + "Bulb", (x, ceil_y - drop - 0.17, z), 0.045, BULB)
	light(name + "L", "POINT", (x, ceil_y - drop - 0.25, z), energy, color, 0.08)


# --- дополнительные материалы ---------------------------------------------------------
TILE_NS = brick_mat("tile_ns", (0, 2), (0.72, 0.74, 0.75), (0.66, 0.69, 0.7), (0.3, 0.3, 0.31), 0.15, 0.15, 0.15)
TILE_EW = brick_mat("tile_ew", (1, 2), (0.72, 0.74, 0.75), (0.66, 0.69, 0.7), (0.3, 0.3, 0.31), 0.15, 0.15, 0.15)
TILE_FLOOR = brick_mat("tile_floor", (0, 1), (0.06, 0.06, 0.07), (0.1, 0.1, 0.11), (0.02, 0.02, 0.02), 0.3, 0.3, 0.3)
KITCHEN_FLOOR = brick_mat("kitchen_floor", (0, 1), (0.35, 0.12, 0.08), (0.3, 0.1, 0.07), (0.1, 0.1, 0.1), 0.2, 0.2, 0.5)
PARQUET = brick_mat("parquet", (0, 1), (0.2, 0.1, 0.045), (0.15, 0.075, 0.035), (0.05, 0.03, 0.02), 0.9, 0.12, 0.35)
PORCELAIN = mat("porcelain", (0.9, 0.9, 0.92), 0.1)
CARPET = mat("carpet", (0.09, 0.03, 0.1), 0.95)
FELT = mat("felt", (0.02, 0.22, 0.12), 0.9)
VELVET_B = mat("velvet_blue", (0.02, 0.04, 0.16), 0.8, sheen=1.0)
GLASS_RAIL = mat("glass_rail", (0.7, 0.85, 1.0), 0.05, trans=0.95)
PLANK = mat("plank", (0.12, 0.07, 0.035), 0.8)
FIELD = mat("field_glow", (0.1, 0.9, 0.8), 0.3, emit=(0.15, 0.95, 0.85), strength=4)
FIRE = mat("fire", (1, 0.4, 0.1), 0.3, emit=(1.0, 0.38, 0.08), strength=30)
WALL2 = mat("wall_plaster_dark", (0.05, 0.035, 0.05), 0.75)
FOOD_RED = mat("currywurst", (0.45, 0.06, 0.02), 0.4)
FOOD_YEL = mat("pommes", (0.85, 0.6, 0.15), 0.6)
PLANT = mat("plant", (0.03, 0.18, 0.05), 0.7)

# ======================================================================================
# ОБОЛОЧКА
# ======================================================================================
group("F1")
box("Floor", (0, -0.25, 0), (W + 1, 0.5, D + 1), FLOOR)
# север: проём двери кухни (x -7.65..-6.75) и окно выдачи (x -5.4..-4.4, y 1.0..1.9)
wall_holes_x("WallN1", -hz - 0.25, -hx - 0.5, hx + 0.5, 0, H + 0.15, 0.5, BRICK_NS,
	[(-7.65, -6.75, 0, 2.1), (-5.4, -4.4, 1.0, 1.9)])
wall_z("WallW1", -hx - 0.25, -hz - 0.5, hz + 0.5, 0, H + 0.15, 0.5, BRICK_EW)
group("CUT1")
wall_holes_x("WallS1", hz + 0.25, -hx - 0.5, hx + 0.5, 0, H + 0.15, 0.5, BRICK_NS, [(-0.8, 0.8, 0, 2.3)])
wall_z("WallE1", hx + 0.25, -hz - 0.5, hz + 0.5, 0, H + 0.15, 0.5, BRICK_EW)
group("F1")
for n, c, s in [("BaseN", (0, 0.1, -hz + 0.02), (W, 0.2, 0.04)), ("BaseW", (-hx + 0.02, 0.1, 0), (0.04, 0.2, D))]:
	box(n, c, s, DARKSTEEL)
box("NeonEdgeN", (0, H - 0.05, -hz + 0.06), (W - 0.2, 0.04, 0.04), NEON_B)
box("NeonEdgeW", (-hx + 0.06, H - 0.05, 0), (0.04, 0.04, D - 0.2), NEON_B)
group("SLAB")
for i, z in enumerate([-3.0, 0.5, 3.6]):
	box("Beam%d" % i, (-3.5 if z < -1.4 else 0, H - 0.18, z), (9.0 if z < -1.4 else W, 0.36, 0.22), DARKSTEEL)

group("F1")
# перекрытие с проёмами: лестница (x -7.4..-1.4, z 5..6) и второй свет над сценой (x 1..8, z -6..-1.4)
group("SLAB")
SLAB_PARTS = [(-8, 1, -6, -1.4), (-8, 8, -1.4, 5.0), (-8, -7.4, 5.0, 6.0), (-1.4, 8, 5.0, 6.0)]
for i, (x0, x1, z0, z1) in enumerate(SLAB_PARTS):
	box("Slab%d" % i, ((x0 + x1) / 2, (H + F2) / 2, (z0 + z1) / 2), (x1 - x0, F2 - H, z1 - z0), CEIL)
box("SlabEdgeStage", (4.5, H + 0.15, -1.38), (7.0, 0.3, 0.04), DARKSTEEL)
box("SlabEdgeStageLED", (4.5, H - 0.02, -1.36), (7.0, 0.03, 0.03), NEON_B)

group("F2")
for i, (x0, x1, z0, z1) in enumerate(SLAB_PARTS):
	box("Parquet%d" % i, ((x0 + x1) / 2, F2 + 0.005, (z0 + z1) / 2), (x1 - x0, 0.01, z1 - z0), PARQUET)
wall_x("WallN2", -hz - 0.25, -hx - 0.5, hx + 0.5, H + 0.15, TOP + 0.3, 0.5, BRICK_NS)
wall_z("WallW2", -hx - 0.25, -hz - 0.5, hz + 0.5, H + 0.15, TOP + 0.3, 0.5, BRICK_EW)
box("NeonEdgeN2", (0, TOP - 0.05, -hz + 0.06), (W - 0.2, 0.04, 0.04), NEON_B)
box("NeonEdgeW2", (-hx + 0.06, TOP - 0.05, 0), (0.04, 0.04, D - 0.2), NEON_B)
group("CUT2")
wall_x("WallS2", hz + 0.25, -hx - 0.5, hx + 0.5, H + 0.15, TOP + 0.3, 0.5, BRICK_NS)
wall_z("WallE2", hx + 0.25, -hz - 0.5, hz + 0.5, H + 0.15, TOP + 0.3, 0.5, BRICK_EW)
group("ROOF")
box("Roof", (0, TOP + 0.25, 0), (W + 1, 0.5, D + 1), CEIL)
for i, z in enumerate([-4.0, -0.5, 3.0]):
	box("Beam2_%d" % i, (0, TOP - 0.18, z), (W, 0.36, 0.22), DARKSTEEL)

# ======================================================================================
# 1 ЭТАЖ — из первого варианта бара (стойка, сцена, вход), без кабинки и диванов у южной стены
# ======================================================================================
group("F1")
# --- вывеска клуба (title_key на (0, 3, -5.95)) ----------------------------------------
text("SignTitle", "NEON", (-1.6, 3.05, -hz + 0.08), 0.75, NEON_B, extrude=0.03)
text("SignSub", "BLAU · WEISS 04", (-1.6, 2.45, -hz + 0.08), 0.28, NEON_W, extrude=0.02)
box("SignBack", (-1.6, 2.8, -hz + 0.03), (3.6, 1.5, 0.04), BLACK)

# --- стойка (коллизия BarCounter: центр (-6.2, 0.55, -1.2), 1.0 × 1.1 × 7.0) ------------
BX, BZ, BL = -6.2, -1.2, 7.0
box("BarBody", (BX, 0.5, BZ), (0.9, 1.0, BL), WOOD)
box("BarTop", (BX + 0.08, 1.07, BZ), (1.16, 0.06, BL + 0.16), mat("granite", (0.02, 0.02, 0.025), 0.12))
box("BarLED", (BX + 0.47, 0.96, BZ), (0.02, 0.03, BL), NEON_B)
box("BarKick", (BX + 0.46, 0.06, BZ), (0.02, 0.1, BL), WARM)
cyl("FootRail", (BX + 0.62, 0.22, BZ), 0.025, BL, STEEL, axis="Z")
# рабочая полка бармена со стороны стены
box("BarWell", (BX - 0.4, 0.85, BZ), (0.2, 0.05, BL - 0.4), DARKSTEEL)
# пивная колонна (перед рабочим местом бармена, z -1.2)
for i, dz in enumerate([-0.3, -0.1, 0.1, 0.3]):
	cyl("Tap%d" % i, (BX - 0.05, 1.32, BZ + dz), 0.02, 0.45, STEEL)
	cyl("TapHandle%d" % i, (BX + 0.02, 1.62, BZ + dz), 0.018, 0.16, BLACK if i % 2 else NEON_W)
box("TapTower", (BX - 0.05, 1.5, BZ), (0.08, 0.08, 0.8), STEEL)
box("DripTray", (BX + 0.05, 1.11, BZ), (0.18, 0.02, 0.8), DARKSTEEL)
# касса (z +1.5) и стаканы
box("Register", (BX - 0.1, 1.22, BZ + 2.7), (0.35, 0.25, 0.4), BLACK)
box("RegisterScreen", (BX + 0.02, 1.42, BZ + 2.7), (0.02, 0.18, 0.28), NEON_W)
for i in range(6):
	cyl("Glass%d" % i, (BX + 0.25, 1.16, BZ - 2.6 + i * 0.13), 0.035, 0.12, BOTTLE[2])
# окошко скупки (Ankauf, x -4.9 z 0.5) — табличка на стойке
box("AnkaufPlate", (BX + 0.25, 1.16, 0.5), (0.25, 0.12, 0.4), BLACK)
text("AnkaufTxt", "ANKAUF", (BX + 0.38, 1.17, 0.5), 0.08, NEON_W, rot_y=math.pi / 2, extrude=0.003)

# --- задняя стенка бара (декор, x -8..-7.6) ------------------------------------------
box("BackCounter", (-7.78, 0.45, BZ), (0.42, 0.9, 6.4), WOOD)
box("BackTop", (-7.78, 0.92, BZ), (0.44, 0.04, 6.4), STEEL)
box("Fridge", (-7.78, 0.45, BZ + 2.4), (0.4, 0.8, 1.2), DARKSTEEL)
box("FridgeGlow", (-7.56, 0.45, BZ + 2.4), (0.01, 0.6, 1.0), WARM)
box("Sink", (-7.78, 0.93, BZ - 1.6), (0.36, 0.03, 0.5), STEEL)
box("CoffeeMachine", (-7.8, 1.12, BZ + 1.2), (0.35, 0.35, 0.45), STEEL)
box("BackMirror", (-7.97, 2.0, BZ), (0.02, 1.4, 5.2), MIRROR)
for i, y in enumerate([1.45, 1.95, 2.45]):
	box("Shelf%d" % i, (-7.82, y, BZ), (0.3, 0.03, 5.6), STEEL)
	box("ShelfLED%d" % i, (-7.68, y - 0.025, BZ), (0.01, 0.01, 5.6), WARM)
	for k in range(24):
		z = BZ - 2.6 + k * 0.225
		m = BOTTLE[(k * 7 + i * 3) % len(BOTTLE)]
		hb = 0.24 + ((k * 13 + i * 5) % 4) * 0.025
		cyl("Bottle%d_%d" % (i, k), (-7.82, y + 0.015 + hb / 2, z), 0.035, hb, m, verts=12)
		cyl("Neck%d_%d" % (i, k), (-7.82, y + 0.015 + hb + 0.04, z), 0.012, 0.08, m, verts=8)
text("BarNeon", "BAR", (-7.93, 3.15, BZ), 0.45, NEON_M, rot_y=math.pi / 2, extrude=0.02)
# служебная дверь за стойкой (северный торец, x -7.2)
box("StaffDoor", (-7.62, 1.05, -6.95), (0.05, 2.1, 0.9), DARKSTEEL)   # дверь кухни открыта внутрь
box("StaffDoorFrame", (-7.2, 2.15, -hz + 0.05), (1.0, 0.1, 0.07), STEEL)
text("StaffSign", "KÜCHE", (-7.2, 2.35, -hz + 0.09), 0.12, NEON_W, extrude=0.004)

# --- барные стулья (между точками «Смена» z -3.0 и «Скупка» z 0.5 оставлены проходы) ---
for i, z in enumerate([-4.2, -2.0, -1.2, -0.4, 1.4, 2.0]):
	x = BX + 0.95
	cyl("StoolBase%d" % i, (x, 0.02, z), 0.2, 0.04, DARKSTEEL)
	cyl("StoolPole%d" % i, (x, 0.38, z), 0.03, 0.7, STEEL)
	cyl("StoolSeat%d" % i, (x, 0.76, z), 0.19, 0.08, LEATHER)
	cyl("StoolRing%d" % i, (x, 0.3, z), 0.16, 0.02, STEEL, r2=0.16)

# --- сцена (StageFloor: центр (4, 0.3, -3.6), 6 × 0.6 × 4.4) ---------------------------
box("Stage", (4.0, 0.3, -3.6), (6.0, 0.6, 4.4), STAGE)
box("StageEdge", (4.0, 0.58, -1.39), (6.0, 0.03, 0.03), NEON_B)
box("StageEdgeW", (0.99, 0.58, -3.6), (0.03, 0.03, 4.4), NEON_B)
box("StageSkirt", (4.0, 0.3, -1.38), (6.0, 0.5, 0.01), NEON_M_SOFT)
# ступени к сцене с запада
box("Step0", (0.85, 0.1, -2.1), (0.3, 0.2, 0.9), DARKSTEEL)
box("Step1", (0.92, 0.3, -2.1), (0.15, 0.2, 0.9), DARKSTEEL)
# ферма над сценой и прожекторы
for x in (1.2, 6.8):
	box("TrussV%.0f" % x, (x, 2.0, -5.6), (0.18, 4.0, 0.18), STEEL, ceiling=True)
box("TrussH", (4.0, 3.55, -3.6), (6.0, 0.18, 0.18), STEEL, ceiling=True)
box("TrussH2", (4.0, 3.55, -5.6), (6.0, 0.18, 0.18), STEEL, ceiling=True)
for i, x in enumerate([2.0, 4.0, 6.0]):
	cyl("Par%d" % i, (x, 3.3, -3.6), 0.12, 0.3, BLACK)
	light("StageSpot%d" % i, "SPOT", (x, 3.2, -3.4), 350 if i != 1 else 450,
		(0.3, 0.5, 1.0) if i != 1 else (1.0, 0.3, 0.7), 0.05, target=(x, 0.6, -3.0), spot_deg=35)
# микрофонная стойка и колонки (16+: музыкальная сцена)
cyl("MicBase", (3.0, 0.62, -2.0), 0.15, 0.03, DARKSTEEL)
cyl("MicPole", (3.0, 1.05, -2.0), 0.012, 0.85, DARKSTEEL)
cyl("MicBoom", (3.0, 1.5, -1.8), 0.01, 0.45, DARKSTEEL, axis="Z")
cyl("Mic", (3.0, 1.52, -1.58), 0.025, 0.14, BLACK, axis="Z", r2=0.035)
box("DJDesk", (5.4, 1.05, -4.6), (1.6, 0.9, 0.6), BLACK)
box("DJDeskLED", (5.4, 0.85, -4.29), (1.6, 0.03, 0.01), NEON_B)
for x in (1.4, 6.6):
	box("Speaker%.0f" % x, (x, 1.2, -5.3), (0.6, 1.2, 0.5), BLACK)
	cyl("Cone%.0f" % x, (x, 1.35, -5.04), 0.18, 0.02, DARKSTEEL, axis="Z")
	cyl("ConeS%.0f" % x, (x, 0.9, -5.04), 0.09, 0.02, DARKSTEEL, axis="Z")
text("StageSign", "LIVE", (4.0, 2.6, -hz + 0.08), 0.4, NEON_M, extrude=0.02)
# точка чаевых (Tip, x 7.2 z -0.4): банка на стойке-тумбе
box("TipStand", (7.2, 0.5, -1.0), (0.4, 1.0, 0.4), DARKSTEEL)
cyl("TipJar", (7.2, 1.1, -1.0), 0.08, 0.2, BOTTLE[2])
text("TipTxt", "TIPS", (7.2, 0.8, -0.79), 0.09, NEON_W, extrude=0.003)

# --- зал: высокие столики и диваны у южной стены (декор; в игре — с коллизией) ---------
for i, (x, z) in enumerate([(-2.6, -3.2), (-2.6, -0.2), (0.4, 1.6)]):
	cyl("TblBase%d" % i, (x, 0.02, z), 0.25, 0.04, DARKSTEEL)
	cyl("TblPole%d" % i, (x, 0.55, z), 0.04, 1.05, STEEL)
	cyl("TblTop%d" % i, (x, 1.08, z), 0.38, 0.04, WOOD)
	cyl("TblCandle%d" % i, (x, 1.13, z), 0.03, 0.06, BULB)
# шахтёрские лампы над залом
for i, (x, z) in enumerate([(-3.0, -2.0), (-3.0, 1.5), (0.0, -0.5), (1.5, 3.0), (-5.5, 4.7)]):
	cyl("LampCord%d" % i, (x, H - 0.4, z), 0.006, 0.8, BLACK, verts=6, ceiling=True)
	cyl("LampShade%d" % i, (x, H - 0.85, z), 0.22, 0.18, DARKSTEEL, r2=0.05, ceiling=True)
	sphere("LampBulb%d" % i, (x, H - 0.95, z), 0.05, BULB, ceiling=True)
	light("LampL%d" % i, "POINT", (x, H - 1.0, z), 45, (1.0, 0.72, 0.45), 0.08)
# лампы над стойкой
for i in range(4):
	z = BZ - 2.6 + i * 1.75
	cyl("BarLampCord%d" % i, (BX, H - 0.5, z), 0.006, 1.0, BLACK, verts=6, ceiling=True)
	cyl("BarLamp%d" % i, (BX, H - 1.05, z), 0.12, 0.25, NEON_W, r2=0.05, ceiling=True)
	light("BarLampL%d" % i, "SPOT", (BX, H - 1.2, z), 70, (1.0, 0.8, 0.6), 0.05, target=(BX, 1.0, z), spot_deg=70)

# --- вход: шлюз «Оставшихся» (южная стена, x 0; ENTRY (0, 4.2), Exit (0, 5.6)) ---------
box("DoorFrameL", (-0.75, 1.15, hz - 0.08), (0.15, 2.3, 0.16), STRIPES)
box("DoorFrameR", (0.75, 1.15, hz - 0.08), (0.15, 2.3, 0.16), STRIPES)
box("DoorFrameT", (0, 2.38, hz - 0.08), (1.65, 0.16, 0.16), STRIPES)
box("Door", (0, 1.1, hz - 0.03), (1.35, 2.2, 0.05), DARKSTEEL)
for k in range(9):
	box("StripCurtain%d" % k, (-0.6 + k * 0.15, 1.15, hz - 0.18), (0.13, 2.25, 0.005), mat("pvc", (0.75, 0.8, 0.85), 0.15, trans=0.6))
sphere("SchleuseLamp", (0, 2.62, hz - 0.12), 0.08, GREEN)
text("ExitSign", "AUSGANG · SCHLEUSE", (0, 2.9, hz - 0.03), 0.16, GREEN, rot_y=math.pi, extrude=0.004)
box("FloorMat", (0, 0.005, 4.9), (1.6, 0.01, 1.4), STRIPES)

# --- место работницы бара (ClubWorker: (-7.25, 0, -1.2), лицом на +X, рост 1.78) -------
# Нейтральный манекен-маркер; модель «Farah» встанет сюда после разрешения автора.
cyl("WorkerLegs", (-7.25, 0.45, -1.2), 0.13, 0.9, MANNEQUIN, r2=0.15)
cyl("WorkerTorso", (-7.25, 1.2, -1.2), 0.17, 0.62, MANNEQUIN, r2=0.2)
sphere("WorkerHead", (-7.25, 1.65, -1.2), 0.11, MANNEQUIN)
box("WorkerMark", (-7.25, 0.006, -1.2), (0.6, 0.01, 0.6), NEON_M)


# ======================================================================================
# 1 ЭТАЖ — новое: туалеты (вместо кабинки), лестница, кухня, диван у входа
# ======================================================================================
group("F1")
# --- 2 туалета: блок x 5..8, z 2.6..6 (на месте кабинки) --------------------------------
WC_OUT = mat("wc_wall_out", (0.08, 0.06, 0.09), 0.6)
wall_holes_z("WCWallW", 5.0, 2.5, 6.0, 0, H, 0.2, WC_OUT, [(3.0, 3.9, 0, 2.1), (4.7, 5.6, 0, 2.1)])
wall_x("WCWallN", 2.6, 4.9, 8.0, 0, H, 0.2, WC_OUT)
wall_x("WCPart", 4.3, 5.1, 8.0, 0, H, 0.1, WC_OUT)
box("WCFloor", (6.55, 0.006, 4.35), (2.9, 0.01, 3.3), TILE_FLOOR)
# плитка внутри до 2.1 м
for n, c, s, m in [("TileE", (7.97, 1.05, 4.3), (0.02, 2.1, 3.4), TILE_EW), ("TileN", (6.55, 1.05, 2.71), (2.9, 2.1, 0.02), TILE_NS),
		("TilePa", (6.55, 1.05, 4.24), (2.9, 2.1, 0.02), TILE_NS), ("TilePb", (6.55, 1.05, 4.36), (2.9, 2.1, 0.02), TILE_NS),
		("TileSo", (6.5, 1.05, 5.97), (3.0, 2.1, 0.02), TILE_NS)]:
	box(n, c, s, m)
for k, (zc, sink_z, mir_z, label) in enumerate([(3.45, 2.85, 2.73, "DAMEN"), (5.15, 5.82, 5.95, "HERREN")]):
	cyl("WCBowl%d" % k, (7.55, 0.2, zc), 0.19, 0.4, PORCELAIN, r2=0.16)
	cyl("WCSeat%d" % k, (7.55, 0.41, zc), 0.2, 0.03, PORCELAIN)
	box("WCTank%d" % k, (7.86, 0.65, zc), (0.2, 0.45, 0.42), PORCELAIN)
	box("WCSink%d" % k, (6.3, 0.85, sink_z), (0.5, 0.12, 0.34), PORCELAIN)
	cyl("WCTap%d" % k, (6.3, 1.0, sink_z + (-0.12 if k == 0 else 0.12)), 0.015, 0.2, STEEL, verts=8)
	box("WCMirror%d" % k, (6.3, 1.55, mir_z), (0.6, 0.8, 0.02), MIRROR)
	box("WCMirLED%d" % k, (6.3, 1.98, mir_z), (0.6, 0.03, 0.03), NEON_W)
	text("WCSign%d" % k, label, (4.88, 2.35, zc), 0.14, NEON_W, rot_y=-math.pi / 2, extrude=0.004)
	sphere("WCLamp%d" % k, (4.88, 2.6, zc), 0.05, GREEN)
	light("WCLight%d" % k, "POINT", (6.6, 3.0, zc), 160, (0.85, 0.92, 1.0), 0.2)
box("WCDoor0", (4.92, 1.05, 3.45), (0.05, 2.1, 0.9), DARKSTEEL)              # Damen — закрыта
box("WCDoor1", (5.55, 1.05, 5.56), (0.9, 2.1, 0.05), DARKSTEEL)              # Herren — открыта внутрь
text("WCBig", "WC", (4.88, 3.15, 4.3), 0.3, NEON_B, rot_y=-math.pi / 2, extrude=0.01)

# --- лестница на 2 этаж: вдоль южной стены, низ на западе (x -7.4), верх у входа (x -1.4) ----
N_STEPS = 24
RUN = 6.0 / N_STEPS
RISE = F2 / N_STEPS
for i in range(N_STEPS):
	x0 = -7.4 + i * RUN
	top = (i + 1) * RISE
	box("Step%d" % i, (x0 + RUN / 2, top / 2, 5.5), (RUN, top, 1.0), FLOOR)
	box("StepNose%d" % i, (x0 + 0.015, top - 0.01, 5.5), (0.03, 0.02, 1.0), DARKSTEEL)
	box("StepLED%d" % i, (x0 - 0.002, top - 0.04, 5.5), (0.004, 0.015, 0.94), NEON_B)
for i in range(7):
	x = -7.4 + i * 1.0
	cyl("StairPost%d" % i, (x, (i * 1.0 / RUN) * RISE + 0.52, 5.02), 0.025, 1.05, STEEL, verts=8)
beam("StairRail", (-7.4, 1.05, 5.02), (-1.4, F2 + 1.05, 5.02), 0.03, STEEL)
beam("StairRailMid", (-7.4, 0.55, 5.02), (-1.4, F2 + 0.55, 5.02), 0.012, STEEL)
text("StairSign", "LOUNGE · 1. OG", (-7.95, 2.3, 5.5), 0.16, NEON_B, rot_y=math.pi / 2, extrude=0.004)

# --- диван и столик у входа (к востоку от двери) ----------------------------------------
sofa("EntrySofa", (2.9, 0, 5.5), 2.4, "x", +1, LEATHER)
box("EntryTable", (2.9, 0.2, 4.65), (1.0, 0.4, 0.5), WOOD)

# --- кухня: пристройка x -8..-1.5, z -10..-6 -----------------------------------------
group("F1")
box("KFloor", (-4.75, 0.006, -8.25), (6.5, 0.01, 3.5), KITCHEN_FLOOR)
wall_z("KWallW", -8.25, -10.5, -6.5, 0, H + 0.15, 0.5, BRICK_EW)
wall_holes_x("KWallN", -10.25, -8.5, -1.0, 0, H + 0.15, 0.5, BRICK_NS, [(-2.9, -2.0, 0, 2.1)])
group("CUT1")
wall_z("KWallE", -1.25, -10.5, -6.5, 0, H + 0.15, 0.5, BRICK_EW)
group("ROOF1")
box("KRoof", (-4.75, H + 0.15, -8.25), (7.5, 0.3, 4.5), CEIL)
group("F1")
for n, c, s, m in [("KTileW", (-7.98, 1.1, -8.25), (0.02, 2.2, 3.5), TILE_EW), ("KTileN", (-4.75, 1.1, -9.98), (6.5, 2.2, 0.02), TILE_NS),
		("KTileE", (-1.52, 1.1, -8.25), (0.02, 2.2, 3.5), TILE_EW)]:
	box(n, c, s, m)
# линия готовки у северной стены, вытяжка
box("KRange", (-5.5, 0.45, -9.6), (2.0, 0.9, 0.7), DARKSTEEL)
for k in range(4):
	cyl("KBurner%d" % k, (-6.0 + (k % 2) * 0.55, 0.91, -9.75 + (k // 2) * 0.35), 0.11, 0.02, BLACK)
cyl("KPot", (-5.45, 1.05, -9.4), 0.15, 0.25, STEEL)
box("KFryer", (-4.1, 0.45, -9.6), (0.7, 0.9, 0.7), STEEL)
box("KFryerOil", (-4.1, 0.88, -9.6), (0.5, 0.02, 0.45), mat("oil", (0.5, 0.35, 0.05), 0.05))
box("KGrill", (-3.05, 0.45, -9.6), (1.2, 0.9, 0.7), STEEL)
box("KGrillTop", (-3.05, 0.91, -9.6), (1.1, 0.02, 0.6), BLACK)
for k in range(4):
	beam("KWurst%d" % k, (-3.4 + k * 0.22, 0.95, -9.75), (-3.4 + k * 0.22, 0.95, -9.45), 0.025, FOOD_RED, verts=8)
box("KHood", (-4.6, 2.3, -9.6), (3.9, 0.4, 0.8), STEEL)
box("KHoodLED", (-4.6, 2.09, -9.6), (3.7, 0.02, 0.5), NEON_W)
box("KDuct", (-4.6, 3.2, -9.85), (0.5, 1.4, 0.3), STEEL)
# холодильник и полки у западной стены
box("KFridge", (-7.6, 1.0, -9.2), (0.7, 2.0, 1.2), STEEL)
box("KFridgeHandle", (-7.24, 1.1, -8.75), (0.03, 0.8, 0.03), BLACK)
for k, y in enumerate([1.3, 1.8]):
	box("KShelf%d" % k, (-7.82, y, -7.4), (0.35, 0.03, 1.4), STEEL)
	for j in range(4):
		cyl("KShelfPot%d_%d" % (k, j), (-7.82, y + 0.1, -7.95 + j * 0.37), 0.12, 0.18, STEEL)
# остров для заготовок
box("KIsland", (-4.6, 0.45, -7.9), (2.4, 0.9, 0.8), STEEL)
box("KBoard", (-5.1, 0.92, -7.9), (0.5, 0.03, 0.35), WOOD)
for j in range(3):
	cyl("KBowl%d" % j, (-4.3 + j * 0.35, 0.96, -7.85), 0.12, 0.1, STEEL, r2=0.07)
box("KTicketRail", (-4.6, 1.75, -7.9), (2.0, 0.03, 0.05), STEEL)
# мойка и посудомойка у восточной стены
box("KSink", (-1.85, 0.45, -8.6), (0.6, 0.9, 1.4), STEEL)
box("KSinkBowl", (-1.85, 0.9, -8.6), (0.45, 0.02, 0.5), DARKSTEEL)
cyl("KSinkTap", (-1.65, 1.15, -8.6), 0.02, 0.45, STEEL, verts=8)
box("KDishwasher", (-1.85, 0.45, -7.3), (0.6, 0.9, 0.7), DARKSTEEL)
# окно выдачи в зал: полка, лампы подогрева, тарелки с карривурстом
box("KPassShelf", (-4.9, 1.0, -6.0), (1.1, 0.04, 0.9), STEEL)
for j in range(2):
	cyl("KPlate%d" % j, (-5.15 + j * 0.5, 1.04, -6.0), 0.13, 0.02, PORCELAIN)
	for q in range(3):
		beam("KCurry%d_%d" % (j, q), (-5.25 + j * 0.5 + q * 0.06, 1.07, -6.05), (-5.2 + j * 0.5 + q * 0.06, 1.07, -5.95), 0.018, FOOD_RED, verts=6)
	for q in range(5):
		beam("KPommes%d_%d" % (j, q), (-5.1 + j * 0.5 + q * 0.02, 1.06, -6.08), (-5.1 + j * 0.5 + q * 0.02, 1.07, -5.98), 0.006, FOOD_YEL, verts=4)
for j in range(2):
	cyl("KHeatLamp%d" % j, (-5.15 + j * 0.5, 1.75, -6.0), 0.07, 0.12, RED_LAMP, r2=0.04)
text("KSignHall", "CURRYWURST · POMMES", (-4.9, 2.2, -5.95), 0.13, WARM, extrude=0.004)
text("KBackExit", "NOTAUSGANG", (-2.45, 2.3, -9.97), 0.12, GREEN, extrude=0.003)
box("KBackDoor", (-2.45, 1.05, -10.02), (0.9, 2.1, 0.05), DARKSTEEL)
light("KLight", "AREA", (-4.7, 3.9, -8.2), 260, (0.9, 0.95, 1.0), 3.0, target=(-4.7, 0, -8.2))
light("KHoodLight", "AREA", (-4.6, 2.05, -9.6), 60, (1.0, 0.85, 0.7), 1.0, target=(-4.6, 0, -9.6))

# ======================================================================================
# 2 ЭТАЖ (пол 4.3): лаунж, 3 приватные комнаты, столики с диванами, галерея над сценой, игровая
# ======================================================================================
group("F2")
Y = F2
# --- ограждения проёмов: над сценой (галерея) и над лестницей -----------------------------
railing("RailGal", (1.0, -1.4), (5.0, -1.4), Y)
railing("RailGalW", (1.0, -6.0), (1.0, -1.4), Y)
railing("RailStair", (-7.4, 5.0), (-1.4, 5.0), Y)
railing("RailStairW", (-7.4, 5.0), (-7.4, 6.0), Y)
# галерея: высокие столики у ограждения
for i, x in enumerate([1.9, 3.6]):
	cyl("GalTblBase%d" % i, (x, Y + 0.02, -0.85), 0.22, 0.04, DARKSTEEL)
	cyl("GalTblPole%d" % i, (x, Y + 0.55, -0.85), 0.035, 1.05, STEEL)
	cyl("GalTblTop%d" % i, (x, Y + 1.08, -0.85), 0.32, 0.04, WOOD)
	for s, dx in enumerate((-0.45, 0.45)):
		cyl("GalStool%d_%d" % (i, s), (x + dx, Y + 0.38, -0.65), 0.03, 0.7, STEEL)
		cyl("GalStoolSeat%d_%d" % (i, s), (x + dx, Y + 0.76, -0.65), 0.17, 0.07, LEATHER)
text("GalSign", "GALERIE", (3.0, Y + 2.6, -1.42), 0.22, NEON_W, rot_y=math.pi, extrude=0.01)

# --- игровая: бильярд, кикер, дартс, музыкальный автомат (x -8..1, z -6..-1.4) -----------
box("PoolBody", (-4.2, Y + 0.38, -3.7), (2.6, 0.76, 1.5), WOOD)
box("PoolFelt", (-4.2, Y + 0.77, -3.7), (2.3, 0.02, 1.2), FELT)
for k in range(6):
	cyl("PoolPocket%d" % k, (-5.35 + (k % 3) * 1.15, Y + 0.78, -4.3 + (k // 3) * 1.2), 0.05, 0.02, BLACK)
for k, c in enumerate([(0.9, 0.9, 0.9), (0.9, 0.7, 0.05), (0.7, 0.05, 0.05), (0.05, 0.1, 0.6), (0.02, 0.02, 0.02)]):
	sphere("PoolBall%d" % k, (-3.7 + k * 0.08 - (0.6 if k == 0 else 0), Y + 0.81, -3.65 + (k % 2) * 0.06), 0.028, mat("ball%d" % k, c, 0.1))
beam("PoolCue", (-5.6, Y + 0.85, -3.0), (-4.2, Y + 0.8, -3.55), 0.008, WOOD)
box("PoolLamp", (-4.2, Y + 1.95, -3.7), (2.0, 0.12, 0.4), DARKSTEEL)
box("PoolLampGlow", (-4.2, Y + 1.885, -3.7), (1.9, 0.01, 0.32), BULB)
light("PoolLight", "AREA", (-4.2, Y + 1.85, -3.7), 90, (1.0, 0.85, 0.6), 1.5, target=(-4.2, Y, -3.7))
# кикер
box("KickerBody", (-0.9, Y + 0.55, -4.4), (0.75, 0.35, 1.3), WOOD)
box("KickerField", (-0.9, Y + 0.74, -4.4), (0.68, 0.01, 1.2), FELT)
for k in range(4):
	box("KickerLeg%d" % k, (-1.2 + (k % 2) * 0.6, Y + 0.2, -4.95 + (k // 2) * 1.1), (0.07, 0.4, 0.07), DARKSTEEL)
for k in range(8):
	beam("KickerRod%d" % k, (-1.5, Y + 0.8, -4.95 + k * 0.155), (-0.3, Y + 0.8, -4.95 + k * 0.155), 0.008, STEEL, verts=6)
	cyl("KickerGrip%d" % k, (-1.55 if k % 2 else -0.25, Y + 0.8, -4.95 + k * 0.155), 0.02, 0.1, BLACK, axis="X")
# дартс на северной стене, черта броска
for k, x in enumerate([-7.2, -6.1]):
	cyl("Dart%d" % k, (x, Y + 1.73, -5.97), 0.23, 0.04, BLACK, axis="Z")
	cyl("DartRing%d" % k, (x, Y + 1.73, -5.945), 0.16, 0.01, mat("dart_red", (0.6, 0.03, 0.03), 0.6), axis="Z")
	cyl("DartBull%d" % k, (x, Y + 1.73, -5.935), 0.03, 0.01, mat("dart_green", (0.03, 0.4, 0.08), 0.6), axis="Z")
	light("DartSpot%d" % k, "SPOT", (x, Y + 2.8, -5.2), 40, (1, 0.95, 0.9), 0.05, target=(x, Y + 1.73, -5.97), spot_deg=30)
box("Oche", (-6.65, Y + 0.012, -3.61), (1.8, 0.01, 0.05), NEON_W)
# музыкальный автомат
box("Jukebox", (-2.3, Y + 0.75, -5.65), (0.9, 1.5, 0.6), BLACK)
box("JukeboxArch", (-2.3, Y + 1.15, -5.34), (0.75, 0.6, 0.02), NEON_M)
box("JukeboxPanel", (-2.3, Y + 0.6, -5.34), (0.6, 0.3, 0.02), WARM)
text("GamesSign", "SPIELE", (-4.2, Y + 2.7, -5.94), 0.35, NEON_M, extrude=0.02)
boarded_window("WinGames", -7.98, Y + 1.7, -2.6, 1.2, 1.3, "z", FIELD)

# --- лаунж (x -8..-1.6, z -1.4..4.9): камин, угловой диван, кресла, ковёр -----------------
box("LoungeRug", (-5.6, Y + 0.012, 1.7), (4.2, 0.01, 4.4), CARPET)
box("FireplaceFrame", (-7.83, Y + 0.6, 1.6), (0.34, 1.2, 1.8), BLACK)
box("FireplaceFire", (-7.66, Y + 0.45, 1.6), (0.02, 0.4, 1.3), FIRE)
box("FireplaceTop", (-7.8, Y + 1.22, 1.6), (0.45, 0.05, 2.0), STEEL)
light("FireLight", "POINT", (-7.3, Y + 0.5, 1.6), 80, (1.0, 0.45, 0.15), 0.3)
text("LoungeSign", "LOUNGE", (-7.96, Y + 2.4, 1.6), 0.4, NEON_B, rot_y=math.pi / 2, extrude=0.02)
sofa("LoungeSofaA", (-4.3, Y, 1.4), 3.0, "z", +1, VELVET_B)            # спинкой на восток, лицом к камину
sofa("LoungeSofaB", (-5.9, Y, 3.75), 2.4, "x", +1, VELVET_B)           # спинкой на юг
box("LoungeTable", (-5.9, Y + 0.2, 1.6), (1.2, 0.4, 0.8), WOOD)
for k, (x, z) in enumerate([(-6.8, -0.5), (-5.2, -0.6)]):
	box("Armchair%d" % k, (x, Y + 0.22, z), (0.8, 0.44, 0.8), LEATHER)
	box("ArmchairBack%d" % k, (x, Y + 0.6, z - 0.32), (0.8, 0.7, 0.16), LEATHER)
cyl("FloorLampPole", (-3.6, Y + 0.8, -0.8), 0.02, 1.6, STEEL)
cyl("FloorLampShade", (-3.6, Y + 1.65, -0.8), 0.22, 0.3, WARM, r2=0.15)
light("FloorLampL", "POINT", (-3.6, Y + 1.5, -0.8), 40, (1.0, 0.7, 0.4), 0.2)
for k, (x, z) in enumerate([(-7.6, 4.55), (-7.6, -1.0), (-1.9, 4.5)]):
	cyl("Pot%d" % k, (x, Y + 0.25, z), 0.2, 0.5, DARKSTEEL, r2=0.16)
	sphere("Plant%d" % k, (x, Y + 0.85, z), 0.35, PLANT)

# --- столики с диванами (x -1.2..3.8, z -0.4..3.8): 4 кабинки-«диннера» ------------------
for k, (x, z) in enumerate([(0.4, 0.6), (2.65, 0.6), (0.4, 2.9), (2.65, 2.9)]):
	box("BoothTable%d" % k, (x, Y + 0.74, z), (1.3, 0.04, 0.7), WOOD)
	cyl("BoothTableLeg%d" % k, (x, Y + 0.37, z), 0.05, 0.72, STEEL)
	sofa("BoothBenchN%d" % k, (x, Y, z - 0.68), 1.5, "x", -1, LEATHER, depth=0.55)
	sofa("BoothBenchS%d" % k, (x, Y, z + 0.68), 1.5, "x", +1, LEATHER, depth=0.55)
	pendant("BoothLamp%d" % k, x, z, TOP, 1.4, NEON_W, 35)
	cyl("BoothCandle%d" % k, (x, Y + 0.79, z), 0.03, 0.06, BULB)
group("CUT2")
boarded_window("WinTables", 1.5, Y + 1.7, 5.98, 1.4, 1.3, "x", FIELD)
group("F2")

# --- площадка у лестницы: гардероб ---------------------------------------------------
cyl("CoatPole", (0.6, Y + 0.9, 5.6), 0.025, 1.8, STEEL)
for k in range(4):
	beam("CoatHook%d" % k, (0.6, Y + 1.75, 5.6), (0.6 + 0.2 * math.cos(k * 1.57), Y + 1.82, 5.6 + 0.2 * math.sin(k * 1.57)), 0.01, STEEL, verts=6)
box("Coat", (0.75, Y + 1.35, 5.6), (0.08, 0.8, 0.4), mat("coat", (0.25, 0.22, 0.18), 0.9))

# --- 3 приватные комнаты (x 5..8, z -1.4..6), коридор x 4..5 ------------------------------
ROOM_WALL = mat("room_wall", (0.1, 0.03, 0.06), 0.7)
ROOMS = [(-1.4, 1.1, (0.25, 0.45, 1.0), "1"), (1.1, 3.55, (1.0, 0.2, 0.6), "2"), (3.55, 6.0, (1.0, 0.35, 0.15), "3")]
holes = [((z0 + z1) / 2 - 0.45, (z0 + z1) / 2 + 0.45, Y, Y + 2.1) for z0, z1, _, _ in ROOMS]
wall_holes_z("RoomWallW", 5.0, -1.5, 6.0, Y, TOP, 0.2, ROOM_WALL, holes)
wall_x("RoomWallN", -1.4, 4.9, 8.0, Y, TOP, 0.2, ROOM_WALL)
for z in (1.1, 3.55):
	wall_x("RoomSep%.1f" % z, z, 5.1, 8.0, Y, TOP, 0.12, ROOM_WALL)
for k, (z0, z1, col, num) in enumerate(ROOMS):
	zc = (z0 + z1) / 2
	box("RoomCarpet%d" % k, (6.55, Y + 0.012, zc), (2.85, 0.01, z1 - z0 - 0.15), CARPET)
	sofa("RoomSofa%d" % k, (7.5, Y, zc), 1.9, "z", +1, VELVET)
	box("RoomTable%d" % k, (6.5, Y + 0.2, zc), (0.6, 0.4, 0.9), WOOD)
	box("RoomLED%d" % k, (7.95, Y + 2.9, zc), (0.02, 0.03, z1 - z0 - 0.3), mat("room_led%d" % k, col, 0.3, emit=col, strength=10))
	light("RoomLight%d" % k, "POINT", (6.6, Y + 2.6, zc), 55, col, 0.3)
	group("CUT2")
	boarded_window("WinRoom%d" % k, 7.98, Y + 1.9, zc, 1.0, 0.9, "z", FIELD)
	group("F2")
	# вход: штора (у комнаты 3 отдёрнута), номер и лампа «свободно/занято»
	if k == 2:
		box("RoomCurtain%d" % k, (4.87, Y + 1.1, zc - 0.33), (0.04, 2.15, 0.25), VELVET)
	else:
		box("RoomCurtain%d" % k, (4.87, Y + 1.1, zc), (0.04, 2.15, 0.9), VELVET)
	box("RoomFrame%d" % k, (4.86, Y + 2.17, zc), (0.06, 0.08, 1.0), STEEL)
	text("RoomNum%d" % k, num, (4.86, Y + 2.55, zc), 0.3, NEON_M, rot_y=-math.pi / 2, extrude=0.01)
	sphere("RoomLamp%d" % k, (4.85, Y + 2.55, zc + 0.35), 0.05, GREEN if k != 1 else RED_LAMP)
text("RoomsSign", "PRIVAT", (4.86, Y + 3.1, 2.3), 0.22, NEON_M, rot_y=-math.pi / 2, extrude=0.01)

# --- общий свет 2 этажа ---------------------------------------------------------------
light("F2Fill", "AREA", (-1.0, TOP - 0.2, 1.0), 260, (1.0, 0.8, 0.65), 9.0)
for k, (x, z) in enumerate([(-6.6, -2.2), (-1.5, -3.2), (-4.5, 1.5)]):
	pendant("F2Lamp%d" % k, x, z, TOP, 1.2)

# мелкий реквизит (раздел C): бутылки, бокалы, меню, постеры, кухня, WC, кабели, износ пола
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "club_props.py"), encoding="utf-8").read())

# ======================================================================================
# СВЕТ 1 ЭТАЖА, МИР, РЕНДЕР
# ======================================================================================
group("F1")
light("AmbientFill", "AREA", (0, 3.8, 0), 200, (0.55, 0.65, 1.0), 8.0)
light("BarWarm", "AREA", (-7.0, 3.2, -1.2), 120, (1.0, 0.7, 0.45), 2.0, target=(-7.0, 0, -1.2))
light("NeonA", "POINT", (-5, 3, -2), 120, (0.2, 0.55, 1.0), 0.2)
light("NeonB", "POINT", (4, 3, -3), 140, (0.2, 0.55, 1.0), 0.2)
world = bpy.data.worlds.new("w")
world.color = (0.002, 0.002, 0.003)
sc.world = world

sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 16 if QUICK else 48
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 6
sc.cycles.transmission_bounces = 4
sc.cycles.caustics_reflective = False
sc.cycles.caustics_refractive = False
sc.render.resolution_percentage = 50 if QUICK else 100
try:
	sc.view_settings.view_transform = "AgX"
	sc.view_settings.look = "AgX - Medium High Contrast"
except Exception:
	pass
sc.view_settings.exposure = 0.3

cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
sc.collection.objects.link(cam)
sc.camera = cam


def shoot(name, pos, target, lens=20, hide=(), size=(1280, 720)):
	if ONLY and ONLY not in name:
		return
	for n, c in COLS.items():
		c.hide_render = n in hide
	sc.render.resolution_x, sc.render.resolution_y = size
	cam.location = g2b(*pos)
	cam.rotation_euler = (g2b(*target) - cam.location).to_track_quat("-Z", "Y").to_euler()
	cam.data.type = "PERSP"
	cam.data.lens = lens
	cam.data.clip_end = 200
	sc.render.filepath = os.path.join(OUT, name + ".png")
	bpy.ops.render.render(write_still=True)
	print("[club2] rendered", name, flush=True)


AXO1 = ("F2", "SLAB", "ROOF", "ROOF1", "CUT1", "CUT2")
AXO2 = ("ROOF", "ROOF1", "CUT1", "CUT2")
shoot("c2_01_f1_axo", (8.0, 21.0, 12.0), (-1.0, 0.0, -2.6), 22, AXO1, (1280, 900))
shoot("c2_02_f2_axo", (11.0, 19.0, 13.5), (-0.5, 4.3, -0.5), 22, AXO2, (1280, 900))
shoot("c2_03_f1_stairs", (0.8, 2.0, -3.2), (-5.0, 1.3, 5.0), 16)
shoot("c2_04_f1_kitchen_door", (-3.3, 1.6, -0.8), (-6.2, 1.3, -6.0), 20)
shoot("c2_05_f1_kitchen", (-1.9, 1.6, -6.7), (-6.3, 1.0, -9.2), 18)
shoot("c2_06_f1_toilets", (2.2, 1.7, 1.2), (6.3, 1.2, 5.2), 18)
shoot("c2_07_f2_lounge", (-0.2, F2 + 1.6, 4.4), (-6.5, F2 + 0.8, 0.3), 16)
shoot("c2_08_f2_gallery", (-0.6, F2 + 1.7, 0.4), (4.5, 0.8, -4.0), 18)
shoot("c2_09_f2_games", (0.5, F2 + 1.7, -1.8), (-5.5, F2 + 0.6, -4.3), 16)
shoot("c2_10_f2_private", (5.35, F2 + 1.55, 5.65), (7.7, F2 + 0.6, 3.9), 16)
shoot("c2_11_f2_tables", (-1.1, F2 + 1.65, 4.6), (3.6, F2 + 0.6, 0.0), 18)
shoot("c2_12_bar_detail", (-5.1, 1.45, -0.2), (-7.6, 1.6, -1.7), 28)
shoot("c2_13_hatch_detail", (-3.7, 1.6, -3.9), (-4.9, 1.8, -6.0), 24)
shoot("c2_14_wc_detail", (7.6, 1.6, 5.8), (5.8, 1.3, 4.3), 18)
shoot("c2_15_table_detail", (1.6, F2 + 1.3, 1.6), (0.4, F2 + 0.75, 0.6), 30)
if not ONLY:
	bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "neon_club_2f.blend"))
print("[club2] done", flush=True)
