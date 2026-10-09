# Прорисовка бара «Neon Bar» (16+) по планировке scenes/club/ClubRoom.gd.
# Запуск: python build_bar.py <папка вывода> [--quick]   (Blender как модуль bpy)
#     или: blender -b -P build_bar.py -- <папка вывода> [--quick]
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


def brick_mat(name, axes):
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
	br.inputs["Color1"].default_value = (0.22, 0.07, 0.045, 1)
	br.inputs["Color2"].default_value = (0.13, 0.05, 0.04, 1)
	br.inputs["Mortar"].default_value = (0.05, 0.05, 0.05, 1)
	br.inputs["Scale"].default_value = 1.0
	br.inputs["Mortar Size"].default_value = 0.012
	br.inputs["Brick Width"].default_value = 0.25
	br.inputs["Row Height"].default_value = 0.075
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
	b.inputs["Roughness"].default_value = 0.85
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


# --- оболочка (как _build_shell: 16 × 4 × 12) -------------------------------------------
W, H, D = 16.0, 4.0, 12.0
hx, hz = W / 2, D / 2
box("Floor", (0, -0.25, 0), (W + 1, 0.5, D + 1), FLOOR)
box("Ceiling", (0, H + 0.25, 0), (W + 1, 0.5, D + 1), CEIL, ceiling=True)
box("WallN", (0, H / 2, -hz - 0.25), (W + 1, H, 0.5), BRICK_NS)
box("WallS", (0, H / 2, hz + 0.25), (W + 1, H, 0.5), BRICK_NS, ceiling=True)
box("WallW", (-hx - 0.25, H / 2, 0), (0.5, H, D + 1), BRICK_EW)
box("WallE", (hx + 0.25, H / 2, 0), (0.5, H, D + 1), BRICK_EW, ceiling=True)
# цоколь из стали по периметру
for n, c, s in [("BaseN", (0, 0.1, -hz + 0.02), (W, 0.2, 0.04)), ("BaseW", (-hx + 0.02, 0.1, 0), (0.04, 0.2, D)),
		("BaseE", (hx - 0.02, 0.1, 0), (0.04, 0.2, D)), ("BaseS", (0, 0.1, hz - 0.02), (W, 0.2, 0.04))]:
	box(n, c, s, DARKSTEEL)
# стальные балки перекрытия (шахтный подвал) и трубы
for i, z in enumerate([-3.0, 0.5, 4.0]):
	box("Beam%d" % i, (0, H - 0.18, z), (W, 0.36, 0.22), DARKSTEEL, ceiling=True)
cyl("PipeA", (0, H - 0.5, -5.6), 0.09, W, STEEL, axis="X", ceiling=True)
cyl("PipeB", (0, H - 0.75, -5.6), 0.06, W, DARKSTEEL, axis="X", ceiling=True)
# неоновый контур под потолком (сине-белый — цвета Blau-Weiß)
box("NeonEdgeN", (0, H - 0.05, -hz + 0.06), (W - 0.2, 0.04, 0.04), NEON_B)
box("NeonEdgeW", (-hx + 0.06, H - 0.05, 0), (0.04, 0.04, D - 0.2), NEON_B)
box("NeonEdgeE", (hx - 0.06, H - 0.05, 0), (0.04, 0.04, D - 0.2), NEON_B, ceiling=True)

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
box("StaffDoor", (-7.2, 1.05, -hz + 0.04), (0.9, 2.1, 0.06), DARKSTEEL)
box("StaffDoorFrame", (-7.2, 2.15, -hz + 0.05), (1.0, 0.1, 0.07), STEEL)
text("StaffSign", "PERSONAL", (-7.2, 2.35, -hz + 0.09), 0.12, NEON_W, extrude=0.004)

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

# --- кабинка (BoothW x=5, z 2.6..6; BoothN z=2.6, x 4.9..8.1) --------------------------
box("BoothW", (5.0, H / 2, 4.3), (0.2, H, 3.4), BOOTH)
box("BoothN", (6.5, H / 2, 2.6), (3.2, H, 0.2), BOOTH)
box("BoothCurtain", (4.88, 1.1, 4.2), (0.04, 2.2, 1.0), VELVET)
box("BoothFrame", (4.87, 2.25, 4.2), (0.06, 0.1, 1.15), STEEL)
sphere("BoothLamp", (4.85, 2.55, 4.2), 0.07, RED_LAMP)
text("BoothSign", "KABINE", (4.86, 2.8, 4.2), 0.16, NEON_M, rot_y=-math.pi / 2, extrude=0.004)
box("BoothSofa", (7.5, 0.25, 4.5), (0.7, 0.5, 2.6), VELVET)
box("BoothSofaBack", (7.85, 0.65, 4.5), (0.15, 0.8, 2.6), VELVET)
light("BoothLight", "POINT", (6.5, 2.8, 4.3), 40, (1.0, 0.3, 0.35), 0.3)

# --- зал: высокие столики и диваны у южной стены (декор; в игре — с коллизией) ---------
for i, (x, z) in enumerate([(-2.6, -3.2), (-2.6, -0.2), (0.4, 1.6)]):
	cyl("TblBase%d" % i, (x, 0.02, z), 0.25, 0.04, DARKSTEEL)
	cyl("TblPole%d" % i, (x, 0.55, z), 0.04, 1.05, STEEL)
	cyl("TblTop%d" % i, (x, 1.08, z), 0.38, 0.04, WOOD)
	cyl("TblCandle%d" % i, (x, 1.13, z), 0.03, 0.06, BULB)
for i, x in enumerate([-6.6, -4.4]):
	box("Sofa%d" % i, (x, 0.22, 5.55), (2.0, 0.44, 0.8), LEATHER)
	box("SofaBack%d" % i, (x, 0.6, 5.9), (2.0, 0.75, 0.2), LEATHER)
	box("LowTable%d" % i, (x, 0.2, 4.7), (0.9, 0.4, 0.5), WOOD)
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

# --- свет и мир ------------------------------------------------------------------------
light("AmbientFill", "AREA", (0, 3.8, 0), 220, (0.55, 0.65, 1.0), 8.0)
light("BarWarm", "AREA", (-7.0, 3.2, -1.2), 120, (1.0, 0.7, 0.45), 2.0, target=(-7.0, 0, -1.2))
light("NeonA", "POINT", (-5, 3, -2), 120, (0.2, 0.55, 1.0), 0.2)    # как в bar_decor.tscn
light("NeonB", "POINT", (4, 3, -3), 140, (0.2, 0.55, 1.0), 0.2)
world = bpy.data.worlds.new("w")
world.color = (0.002, 0.002, 0.003)
sc.world = world

# --- рендер ----------------------------------------------------------------------------
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 16 if QUICK else 64
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 6
sc.cycles.transmission_bounces = 4
sc.cycles.caustics_reflective = False
sc.cycles.caustics_refractive = False
sc.render.resolution_x = 1280
sc.render.resolution_y = 720
sc.render.resolution_percentage = 50 if QUICK else 100
try:
	sc.view_settings.view_transform = "AgX"
	sc.view_settings.look = "AgX - Medium High Contrast"
except Exception:
	pass
sc.view_settings.exposure = 0.3

cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
COL.objects.link(cam)
sc.camera = cam


def shoot(name, pos, target, lens=20, ortho=None):
	cam.location = g2b(*pos)
	cam.rotation_euler = (g2b(*target) - cam.location).to_track_quat("-Z", "Y").to_euler()
	if ortho:
		cam.data.type = "ORTHO"
		cam.data.ortho_scale = ortho
	else:
		cam.data.type = "PERSP"
		cam.data.lens = lens
	sc.render.filepath = os.path.join(OUT, name + ".png")
	bpy.ops.render.render(write_still=True)
	print("[bar] rendered", name, flush=True)


shoot("bar_01_entrance", (1.2, 1.7, 5.3), (-2.5, 1.3, -3.0), lens=16)
shoot("bar_02_counter", (-3.4, 1.6, 2.6), (-7.0, 1.3, -1.8), lens=22)
shoot("bar_03_worker_view", (-7.3, 1.62, -2.9), (2.0, 1.0, 2.0), lens=18)
shoot("bar_04_stage", (-1.5, 1.7, 2.8), (4.5, 1.0, -4.0), lens=20)
for o in CEILING:
	o.hide_render = True
shoot("bar_05_top", (0.0, 30.0, 0.001), (0.0, 0.0, 0.0), ortho=17.5)
sc.render.resolution_x, sc.render.resolution_y = 1280, 900
shoot("bar_06_axo", (9.5, 13.0, 12.0), (-0.5, 0.0, -0.5), lens=24)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "neon_bar.blend"))
print("[bar] done", flush=True)
