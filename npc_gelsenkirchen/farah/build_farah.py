# Фарах Хаддад (≈47), барменша NEON — сборка в MPFB2 (MakeHuman для Blender) + одежда и детали.
# Запуск (Blender как модуль bpy): python build_farah.py <папка mpfb (boot.py, mpfb2, mh)> <папка вывода> [--quick]
# Тело и лицо — настоящий MPFB2 (CC0 база MakeHuman), скелет Mixamo (как у Валентины — те же анимации).
# Глаза — ассет MakeHuman (CC0). Кожа — 4K-текстура Валентины (та же UV-развёртка MakeHuman), перекрашена.
# Причёска, одежда и аксессуары — смоделированы здесь (системных ассетов MakeHuman из облака не скачать).
import sys, os, math, random
MPFB_DIR, OUT = sys.argv[1], sys.argv[2]
QUICK = "--quick" in sys.argv
sys.path.insert(0, MPFB_DIR)
import boot, bpy, bmesh
from mathutils import Vector, Matrix

GAME = "/home/user/pfeffi-game/assets/characters/standin_valentina/"
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
boot.enable()
from mpfb.services.humanservice import HumanService
from mpfb.services.targetservice import TargetService
sc = bpy.context.scene
TG = os.path.join(MPFB_DIR, "mpfb2", "src", "mpfb", "data", "targets")

# --- 1. тело: возраст 47, полноватая, средний рост, средиземноморский тип ----------------------------
AGE = 0.5 + (47 - 25) / (90 - 25) * 0.5          # шкала MakeHuman: 0.5 = 25 лет, 1.0 = 90
macro = {"gender": 0.0, "age": AGE, "muscle": 0.42, "weight": 0.64, "proportions": 0.55, "height": 0.42,
	"cupsize": 0.58, "firmness": 0.32, "race": {"caucasian": 0.72, "african": 0.14, "asian": 0.14}}
body = HumanService.create_human(macro_detail_dict=macro)
body.name = "Farah_Body"

# --- 2. лицо: нос с горбинкой, широкие скулы, крепкий подбородок, тяжеловатые веки --------------------
FACE = {"nose/nose-curve-convex": 0.45, "nose/nose-greek-incr": 0.25, "nose/nose-scale-vert-incr": 0.25, "nose/nose-flaring-incr": 0.15,
	"cheek/l-cheek-bones-incr": 0.35, "cheek/r-cheek-bones-incr": 0.35, "cheek/l-cheek-volume-decr": 0.2, "cheek/r-cheek-volume-decr": 0.2,
	"chin/chin-width-incr": 0.25, "chin/chin-prominent-incr": 0.2, "head/head-oval": 0.4, "head/head-fat-incr": 0.15,
	"eyebrows/eyebrows-trans-down": 0.25, "head/head-age-incr": 0.6, "cheek/l-cheek-trans-down": 0.25, "cheek/r-cheek-trans-down": 0.25, "eyebrows/eyebrows-angle-down": 0.15, "mouth/mouth-scale-horiz-incr": 0.15,
	"mouth/mouth-angles-down": 0.15, "mouth/mouth-laugh-lines-in": 0.4, "neck/neck-scale-horiz-incr": 0.1}
for rel, w in FACE.items():
	p = os.path.join(TG, rel + ".target.gz")
	if os.path.exists(p):
		TargetService.load_target(body, p, weight=w)
	else:
		print("[farah] нет цели", rel)

# --- 3. глаза (ассет MakeHuman) и скелет Mixamo -----------------------------------------------------
eyes = None
try:
	eyes = HumanService.add_mhclo_asset(os.path.join(MPFB_DIR, "mh/makehuman/data/eyes/high-poly/high-poly.mhclo"), body,
		asset_type="Eyes", subdiv_levels=0, material_type="MAKESKIN")
except Exception as e:
	print("[farah] глаза:", repr(e))
rig = HumanService.add_builtin_rig(body, "mixamo")
rig.name = "Farah_Rig"
if eyes:
	eyes.name = "Farah_Eyes"
dg = bpy.context.evaluated_depsgraph_get()


# --- вспомогательное --------------------------------------------------------------------------------
def mat(name, color, rough=0.5, metal=0.0, emit=None, strength=0.0, trans=0.0, sheen=0.0, coat=0.0):
	m = bpy.data.materials.new(name)
	m.use_nodes = True
	b = m.node_tree.nodes["Principled BSDF"]
	b.inputs["Base Color"].default_value = (*color, 1)
	b.inputs["Roughness"].default_value = rough
	b.inputs["Metallic"].default_value = metal
	if emit:
		b.inputs["Emission Color"].default_value = (*emit, 1)
		b.inputs["Emission Strength"].default_value = strength
	b.inputs["Transmission Weight"].default_value = trans
	b.inputs["Sheen Weight"].default_value = sheen
	b.inputs["Coat Weight"].default_value = coat
	return m


def eval_copy(name, keep_face):
	"""Копия тела в позе покоя (с целями MPFB) — только грани, где keep_face(face_vertex_ids) истинно; группы вершин сохраняются."""
	ev = body.evaluated_get(dg)
	me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
	bm = bmesh.new()
	bm.from_mesh(me)
	dl = bm.verts.layers.deform.verify()
	drop = [f for f in bm.faces if not keep_face(f, dl)]
	bmesh.ops.delete(bm, geom=drop, context="FACES")
	bm.to_mesh(me)
	bm.free()
	o = bpy.data.objects.new(name, me)
	sc.collection.objects.link(o)
	for g in body.vertex_groups:
		o.vertex_groups.new(name=g.name)
	return o


GROUP = {g.index: g.name for g in body.vertex_groups}
GI = {g.name: g.index for g in body.vertex_groups}


def dominant(v, dl):
	best, bw = None, 0.0
	for gi, w in v[dl].items():
		n = GROUP.get(gi, "")
		if n.startswith("mixamorig:") and w > bw:
			best, bw = n, w
	return best


def in_body(v, dl):
	return v[dl].get(GI["body"], 0.0) > 0.5


def bone_set_face(bones, need_all=True):
	def f(face, dl):
		ok = [in_body(v, dl) and dominant(v, dl) in bones for v in face.verts]
		return all(ok) if need_all else any(ok) and all(in_body(v, dl) for v in face.verts)
	return f


def inflate(o, off, thick, m, smooth=1):
	me = o.data
	me.update()
	for v in me.vertices:
		v.co += v.normal * off
	sol = o.modifiers.new("Thick", "SOLIDIFY")
	sol.thickness = thick
	sol.offset = 1.0
	arm = o.modifiers.new("Armature", "ARMATURE")
	arm.object = rig
	if smooth:
		sub = o.modifiers.new("Smooth", "SUBSURF")
		sub.levels = smooth
		sub.render_levels = smooth
	me.materials.append(m)
	for p in me.polygons:
		p.use_smooth = True
	o.parent = rig
	return o


def parent_bone(o, bone):
	bpy.context.view_layer.update()
	mw = o.matrix_world.copy()
	o.parent = rig
	o.parent_type = "BONE"
	o.parent_bone = bone
	o.matrix_world = mw


# --- 4. кожа: текстура MakeHuman-развёртки, темнее и оливковее, с мелким рельефом пор ---------------
skin = bpy.data.materials.new("Farah_Skin")
skin.use_nodes = True
nt = skin.node_tree
bsdf = nt.nodes["Principled BSDF"]
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = bpy.data.images.load(GAME + "valentina_standin_valentina_skin_4k.png")
hsv = nt.nodes.new("ShaderNodeHueSaturation")
hsv.inputs["Hue"].default_value = 0.505
hsv.inputs["Saturation"].default_value = 1.05
hsv.inputs["Value"].default_value = 0.62
nt.links.new(tex.outputs["Color"], hsv.inputs["Color"])
tint = nt.nodes.new("ShaderNodeMix")
tint.data_type = "RGBA"
tint.blend_type = "MULTIPLY"
tint.inputs["Factor"].default_value = 0.7
tint.inputs[7].default_value = (0.66, 0.46, 0.33, 1)
nt.links.new(hsv.outputs["Color"], tint.inputs[6])
nt.links.new(tint.outputs[2], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.52
bsdf.inputs["Subsurface Weight"].default_value = 0.12
bsdf.inputs["Subsurface Radius"].default_value = (0.9, 0.45, 0.25)
bsdf.inputs["Subsurface Scale"].default_value = 0.01
pores = nt.nodes.new("ShaderNodeTexNoise")
pores.inputs["Scale"].default_value = 900
pores.inputs["Detail"].default_value = 4
bump = nt.nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.1
bump.inputs["Distance"].default_value = 0.0006
nt.links.new(pores.outputs["Fac"], bump.inputs["Height"])
nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
body.data.materials.clear()
body.data.materials.append(skin)
for p in body.data.polygons:
	p.use_smooth = True

# --- 5. одежда по весам костей (повторяет позу через тот же скелет) --------------------------------
SHIRT_B = {"mixamorig:Spine", "mixamorig:Spine1", "mixamorig:Spine2", "mixamorig:LeftShoulder", "mixamorig:RightShoulder",
	"mixamorig:LeftArm", "mixamorig:RightArm"}
PANTS_B = {"mixamorig:Hips", "mixamorig:LeftUpLeg", "mixamorig:RightUpLeg", "mixamorig:LeftLeg", "mixamorig:RightLeg"}
SHOE_B = {"mixamorig:LeftFoot", "mixamorig:RightFoot", "mixamorig:LeftToeBase", "mixamorig:RightToeBase"}
CLOTH_BLACK = mat("Shirt_Black", (0.018, 0.018, 0.02), 0.78, sheen=0.4)
DENIM = mat("Trousers_Dark", (0.04, 0.045, 0.06), 0.85, sheen=0.2)
SHOE = mat("Shoes_Black", (0.012, 0.011, 0.01), 0.35, coat=0.3)
shirt = inflate(eval_copy("Farah_Shirt", bone_set_face(SHIRT_B, need_all=False)), 0.006, 0.0025, CLOTH_BLACK)
pants = inflate(eval_copy("Farah_Trousers", bone_set_face(PANTS_B)), 0.005, 0.0025, DENIM)
shoes = inflate(eval_copy("Farah_Shoes", bone_set_face(SHOE_B)), 0.011, 0.004, SHOE, smooth=2)

# --- 6. волосы: тугой пучок с проседью ---------------------------------------------------------------
HAIR = bpy.data.materials.new("Hair_GreyStreaks")
HAIR.use_nodes = True
hn = HAIR.node_tree
hb = hn.nodes["Principled BSDF"]
coord = hn.nodes.new("ShaderNodeTexCoord")
wave = hn.nodes.new("ShaderNodeTexWave")
wave.bands_direction = "Z"
wave.inputs["Scale"].default_value = 260
wave.inputs["Distortion"].default_value = 6
wave.inputs["Detail"].default_value = 3
hn.links.new(coord.outputs["Object"], wave.inputs["Vector"])
streak = hn.nodes.new("ShaderNodeTexNoise")
streak.inputs["Scale"].default_value = 35
mp = hn.nodes.new("ShaderNodeMapping")
mp.inputs["Scale"].default_value = (1, 1, 0.15)
hn.links.new(coord.outputs["Object"], mp.inputs[0])
hn.links.new(mp.outputs[0], streak.inputs["Vector"])
ramp = hn.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = 0.62
ramp.color_ramp.elements[0].color = (0.028, 0.019, 0.014, 1)
ramp.color_ramp.elements[1].position = 0.72
ramp.color_ramp.elements[1].color = (0.42, 0.4, 0.38, 1)
hn.links.new(streak.outputs["Fac"], ramp.inputs[0])
hn.links.new(ramp.outputs[0], hb.inputs["Base Color"])
hb.inputs["Roughness"].default_value = 0.72
hb.inputs["Anisotropic"].default_value = 0.35
hb.inputs["Coat Weight"].default_value = 0.15
hbump = hn.nodes.new("ShaderNodeBump")
hbump.inputs["Strength"].default_value = 0.22
hn.links.new(wave.outputs["Fac"], hbump.inputs["Height"])
hn.links.new(hbump.outputs["Normal"], hb.inputs["Normal"])


def scalp_face(face, dl):
	return all(v[dl].get(GI["scalp"], 0.0) > 0.3 for v in face.verts)


cap = inflate(eval_copy("Farah_HairCap", scalp_face), 0.004, 0.004, HAIR, smooth=2)
cv = [cap.matrix_world @ v.co for v in cap.data.vertices]
zmax = max(v.z for v in cv)
ymax = max(v.y for v in cv)
zmin_s = min(v.z for v in cv)
bun_c = Vector((0.0, ymax + 0.025, zmin_s + (zmax - zmin_s) * 0.72))
bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1.0, location=bun_c)
bun = bpy.context.object
bun.name = "Farah_HairBun"
bun.scale = (0.052, 0.045, 0.047)
bun.data.materials.append(HAIR)
bpy.ops.object.shade_smooth()
tw = bun.modifiers.new("Twist", "SIMPLE_DEFORM")
tw.deform_method = "TWIST"
tw.angle = math.radians(120)
parent_bone(bun, "mixamorig:Head")
bpy.ops.mesh.primitive_torus_add(major_radius=0.034, minor_radius=0.006, location=bun_c + Vector((0, -0.012, 0)), rotation=(math.radians(80), 0, 0))
band = bpy.context.object
band.name = "Farah_HairTie"
band.data.materials.append(mat("HairTie", (0.08, 0.02, 0.02), 0.6))
parent_bone(band, "mixamorig:Head")

# --- 7. брови и ресницы — ассеты MakeHuman у Валентины (CC0), подогнаны к лицу Фарах ---------------
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GAME + "valentina_standin.glb")
imported = set(bpy.data.objects) - before
val_eye = next((o for o in imported if o.type == "MESH" and o.name.startswith("high-poly")), None)
brow = next((o for o in imported if o.type == "MESH" and o.name.startswith("eyebrow")), None)
lash = next((o for o in imported if o.type == "MESH" and o.name.startswith("eyelashes")), None)


def center(o):
	pts = [o.matrix_world @ v.co for v in o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices]
	return sum(pts, Vector()) / len(pts), pts


keep = []
if val_eye and eyes:
	dg2 = bpy.context.evaluated_depsgraph_get()
	vc, vp = center(val_eye)
	fc, fp = center(eyes)
	vw = max(p.x for p in vp) - min(p.x for p in vp)
	fw = max(p.x for p in fp) - min(p.x for p in fp)
	k = fw / vw if vw > 0 else 1.0
	for src, nm in ((brow, "Farah_Brows"), (lash, "Farah_Lashes")):
		if not src:
			continue
		ev = src.evaluated_get(dg2)
		me = bpy.data.meshes.new_from_object(ev, depsgraph=dg2)
		me.transform(src.matrix_world)
		for v in me.vertices:
			v.co = fc + (v.co - vc) * k
		o = bpy.data.objects.new(nm, me)
		sc.collection.objects.link(o)
		for m_ in src.data.materials:
			me.materials.append(m_)
		if nm == "Farah_Brows":
			bm_ = bpy.data.materials.new("Brows_Dark")
			bm_.use_nodes = True
			bt = bm_.node_tree.nodes.new("ShaderNodeTexImage")
			bt.image = bpy.data.images.load(GAME + "valentina_standin_eyebrow001.png")
			bp = bm_.node_tree.nodes["Principled BSDF"]
			bp.inputs["Base Color"].default_value = (0.035, 0.026, 0.02, 1)
			bp.inputs["Roughness"].default_value = 0.7
			bm_.node_tree.links.new(bt.outputs["Alpha"], bp.inputs["Alpha"])
			me.materials.clear()
			me.materials.append(bm_)
			sw = o.modifiers.new("Hug", "SHRINKWRAP")
			sw.target = body
			sw.wrap_method = "NEAREST_SURFACEPOINT"
			sw.offset = 0.0012
			for m_ in me.materials:                      # брови темнее и чуть с проседью
				b_ = m_.node_tree.nodes.get("Principled BSDF")
				if b_:
					b_.inputs["Roughness"].default_value = 0.6
		parent_bone(o, "mixamorig:Head")
		keep.append(o)
for o in imported:
	bpy.data.objects.remove(o, do_unlink=True)

# --- 8. фартук NEON с синей полосой, полотенце, серьги, очки, респиратор --------------------------
bev = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
bverts = [body.matrix_world @ v.co for v in bev.data.vertices]


def front_y(z, half_w=0.17, dz=0.02):
	ys = [p.y for p in bverts if abs(p.z - z) < dz and abs(p.x) < half_w]
	return min(ys) if ys else -0.12


zs = [p.z for p in bverts]
H = max(zs)
Z_WAIST, Z_KNEE, Z_CHEST = H * 0.585, H * 0.30, H * 0.735
APRON = bpy.data.materials.new("Apron_NEON")
APRON.use_nodes = True
an = APRON.node_tree
ab = an.nodes["Principled BSDF"]
gc = an.nodes.new("ShaderNodeTexCoord")
sep = an.nodes.new("ShaderNodeSeparateXYZ")
an.links.new(gc.outputs["Generated"], sep.inputs[0])
st = an.nodes.new("ShaderNodeValToRGB")                   # синяя полоса у нижнего края
st.color_ramp.interpolation = "CONSTANT"
st.color_ramp.elements[0].color = (0.012, 0.014, 0.022, 1)
st.color_ramp.elements[1].position = 0.06
st.color_ramp.elements[1].color = (0.012, 0.014, 0.022, 1)
e2 = st.color_ramp.elements.new(0.03)
e2.color = (0.05, 0.25, 0.85, 1)
an.links.new(sep.outputs["Z"], st.inputs[0])
an.links.new(st.outputs[0], ab.inputs["Base Color"])
ab.inputs["Roughness"].default_value = 0.8
ab.inputs["Sheen Weight"].default_value = 0.3
# юбка фартука: сетка по профилю тела спереди
rows, cols, W_ = 16, 10, 0.44
bm = bmesh.new()
grid = []
for r in range(rows + 1):
	z = Z_KNEE + (Z_WAIST - Z_KNEE) * r / rows
	fy = front_y(z, 0.2) - 0.018
	row = []
	for c in range(cols + 1):
		x = -W_ / 2 + W_ * c / cols
		row.append(bm.verts.new((x, fy + 0.085 * (x / (W_ / 2)) ** 2, z)))
	grid.append(row)
uvl = bm.loops.layers.uv.new()
for r in range(rows):
	for c in range(cols):
		f = bm.faces.new((grid[r][c], grid[r][c + 1], grid[r + 1][c + 1], grid[r + 1][c]))
# нагрудник
brows_, bc, BW = 8, 6, 0.26
grid2 = []
for r in range(brows_ + 1):
	z = Z_WAIST + (Z_CHEST - Z_WAIST) * r / brows_
	fy = front_y(z, 0.14) - 0.012
	grid2.append([bm.verts.new((-BW / 2 + BW * c / bc, fy, z)) for c in range(bc + 1)])
for r in range(brows_):
	for c in range(bc):
		bm.faces.new((grid2[r][c], grid2[r][c + 1], grid2[r + 1][c + 1], grid2[r + 1][c]))
ame = bpy.data.meshes.new("Farah_Apron")
bm.to_mesh(ame)
bm.free()
apron = bpy.data.objects.new("Farah_Apron", ame)
sc.collection.objects.link(apron)
ame.materials.append(APRON)
s_ = apron.modifiers.new("Thick", "SOLIDIFY")
s_.thickness = 0.003
ss_ = apron.modifiers.new("Smooth", "SUBSURF")
ss_.levels = 1
for p in ame.polygons:
	p.use_smooth = True
parent_bone(apron, "mixamorig:Hips")
# надпись NEON на нагруднике
bpy.ops.object.text_add(location=(0, front_y((Z_WAIST + Z_CHEST) / 2, 0.14) - 0.016, (Z_WAIST + Z_CHEST) / 2 + 0.03), rotation=(math.radians(90), 0, 0))
neon = bpy.context.object
neon.name = "Farah_ApronLogo"
neon.data.body = "NEON"
neon.data.size = 0.045
neon.data.align_x = "CENTER"
neon.data.extrude = 0.0005
neon.data.materials.append(mat("ApronLogo", (0.2, 0.55, 1.0), 0.5, emit=(0.15, 0.45, 1.0), strength=0.6))
parent_bone(neon, "mixamorig:Spine1")
# полотенце на левом плече (перекинуто)
sh = [p for p in bverts if p.x > 0.1 and p.z > H * 0.8]
top = max(sh, key=lambda p: p.z) if sh else Vector((0.15, 0, H * 0.82))
TOW = bpy.data.materials.new("Towel")
TOW.use_nodes = True
tn = TOW.node_tree
tb = tn.nodes["Principled BSDF"]
tc = tn.nodes.new("ShaderNodeTexCoord")
tw_ = tn.nodes.new("ShaderNodeTexWave")
tw_.inputs["Scale"].default_value = 6
tn.links.new(tc.outputs["Object"], tw_.inputs["Vector"])
tr = tn.nodes.new("ShaderNodeValToRGB")
tr.color_ramp.interpolation = "CONSTANT"
tr.color_ramp.elements[0].color = (0.82, 0.8, 0.75, 1)
tr.color_ramp.elements[1].position = 0.85
tr.color_ramp.elements[1].color = (0.35, 0.12, 0.1, 1)
tn.links.new(tw_.outputs["Fac"], tr.inputs[0])
tn.links.new(tr.outputs[0], tb.inputs["Base Color"])
tb.inputs["Roughness"].default_value = 0.95
tb.inputs["Sheen Weight"].default_value = 1.0
bm = bmesh.new()
pts = []
for i in range(13):                                         # дуга через плечо спереди назад
	t = i / 12
	a = math.pi * t
	y = -math.cos(a) * 0.11
	z = top.z + 0.012 + math.sin(a) * 0.02 - (abs(math.cos(a)) ** 3) * 0.24
	pts.append((top.x - 0.005, y, z))
vs = []
for (x, y, z) in pts:
	vs.append((bm.verts.new((x - 0.045, y, z)), bm.verts.new((x + 0.045, y, z))))
for i in range(len(vs) - 1):
	bm.faces.new((vs[i][0], vs[i][1], vs[i + 1][1], vs[i + 1][0]))
tme = bpy.data.meshes.new("Farah_Towel")
bm.to_mesh(tme)
bm.free()
towel = bpy.data.objects.new("Farah_Towel", tme)
sc.collection.objects.link(towel)
tme.materials.append(TOW)
s_ = towel.modifiers.new("Thick", "SOLIDIFY")
s_.thickness = 0.006
s_.offset = 0
ss_ = towel.modifiers.new("Smooth", "SUBSURF")
ss_.levels = 2
for p in tme.polygons:
	p.use_smooth = True
parent_bone(towel, "mixamorig:LeftShoulder")
# серьги-кольца у мочек
GOLD = mat("Gold", (0.85, 0.62, 0.28), 0.22, 1.0)
def ear_face(face, dl):
	return all(v[dl].get(GI["ears"], 0.0) > 0.5 for v in face.verts)


_ec = eval_copy("tmp_ears", ear_face)
earpts = [v.co.copy() for v in _ec.data.vertices]
bpy.data.objects.remove(_ec, do_unlink=True)
for side in (1, -1):
	sp = [p for p in earpts if p.x * side > 0]
	if not sp:
		continue
	lobe = min(sp, key=lambda p: p.z)
	bpy.ops.mesh.primitive_torus_add(major_radius=0.014, minor_radius=0.0013, location=(lobe.x, lobe.y, lobe.z - 0.014), rotation=(0, math.radians(90), 0))
	o = bpy.context.object
	o.name = "Farah_Earring_%s" % ("L" if side > 0 else "R")
	o.data.materials.append(GOLD)
	bpy.ops.object.shade_smooth()
	parent_bone(o, "mixamorig:Head")
# очки для чтения в вырезе рубашки
zc_ = H * 0.79
yc_ = front_y(zc_, 0.08) - 0.012
FRAME = mat("GlassesFrame", (0.12, 0.05, 0.03), 0.3, coat=0.5)
LENS = mat("GlassesLens", (0.95, 0.97, 1.0), 0.02, trans=1.0)
for dx in (-0.028, 0.028):
	bpy.ops.mesh.primitive_torus_add(major_radius=0.02, minor_radius=0.0018, location=(dx, yc_, zc_), rotation=(math.radians(90), 0, 0))
	o = bpy.context.object
	o.data.materials.append(FRAME)
	parent_bone(o, "mixamorig:Spine2")
	bpy.ops.mesh.primitive_cylinder_add(radius=0.019, depth=0.001, location=(dx, yc_, zc_), rotation=(math.radians(90), 0, 0))
	o = bpy.context.object
	o.data.materials.append(LENS)
	parent_bone(o, "mixamorig:Spine2")
# респиратор на шее (висит на ремешке)
zn = H * 0.795
yn = front_y(zn, 0.06) - 0.025
RESP = mat("Respirator", (0.18, 0.19, 0.2), 0.55)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, yn, zn))
o = bpy.context.object
o.name = "Farah_Respirator"
o.scale = (0.034, 0.02, 0.028)
o.data.materials.append(RESP)
bpy.ops.object.shade_smooth()
parent_bone(o, "mixamorig:Neck")
for dx in (-0.04, 0.04):
	bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.016, location=(dx * 0.75, yn - 0.004, zn - 0.008), rotation=(math.radians(90), 0, math.radians(20 if dx > 0 else -20)))
	o = bpy.context.object
	o.data.materials.append(mat("Filter", (0.55, 0.42, 0.1), 0.5))
	parent_bone(o, "mixamorig:Neck")

sub = body.modifiers.new("Smooth", "SUBSURF")
sub.levels = 1
sub.render_levels = 2

# --- 9. поза: руки вниз, лёгкий изгиб локтей ------------------------------------------------------
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="POSE")


def rot_world(bn, axis, ang):
	pb = rig.pose.bones[bn]
	head = pb.head.copy()
	M = Matrix.Translation(head) @ Matrix.Rotation(ang, 4, axis) @ Matrix.Translation(-head)
	pb.matrix = M @ pb.matrix
	bpy.context.view_layer.update()


rot_world("mixamorig:LeftArm", "Y", math.radians(28))
rot_world("mixamorig:RightArm", "Y", math.radians(-28))
rot_world("mixamorig:Head", "Y", math.radians(2))
bpy.ops.object.mode_set(mode="OBJECT")

# --- 10. студия и рендер -----------------------------------------------------------------------------
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 24 if QUICK else 96
sc.cycles.use_denoising = True
sc.render.resolution_percentage = 50 if QUICK else 100
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Medium High Contrast"
sc.world = bpy.data.worlds.new("w")
sc.world.color = (0.03, 0.03, 0.035)
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
fl = bpy.context.object
fl.data.materials.append(mat("Backdrop", (0.12, 0.12, 0.13), 0.7))
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 3, 5), rotation=(math.radians(90), 0, 0))
bpy.context.object.data.materials.append(mat("BackdropWall", (0.12, 0.12, 0.14), 0.8))


def light(loc, energy, color, size, target):
	ld = bpy.data.lights.new("L", "AREA")
	ld.energy = energy
	ld.color = color
	ld.size = size
	o = bpy.data.objects.new("L", ld)
	sc.collection.objects.link(o)
	o.location = loc
	o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


light((-1.6, -2.2, 2.4), 170, (1.0, 0.93, 0.85), 1.6, (0, 0, 1.2))     # ключ
light((2.0, -1.4, 1.6), 45, (0.75, 0.85, 1.0), 2.0, (0, 0, 1.1))      # заполняющий
light((0.8, 1.8, 2.2), 160, (1.0, 0.85, 0.7), 1.0, (0, 0, 1.4))        # контровой
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
sc.collection.objects.link(cam)
sc.camera = cam


def shoot(name, loc, target, lens, res=(900, 1300)):
	sc.render.resolution_x, sc.render.resolution_y = res
	cam.location = loc
	cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
	cam.data.lens = lens
	sc.render.filepath = os.path.join(OUT, name + ".png")
	bpy.ops.render.render(write_still=True)
	print("[farah] rendered", name, flush=True)


shoot("farah_front", (0, -3.6, 0.95), (0, 0, 0.86), 50)
shoot("farah_34", (2.2, -2.8, 1.1), (0, 0, 0.88), 50)
shoot("farah_face", (0.25, -0.75, H * 0.93), (0, 0, H * 0.925), 85, (900, 900))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "farah_mpfb.blend"))
print("[farah] done", flush=True)
