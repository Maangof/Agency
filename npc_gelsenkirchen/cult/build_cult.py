# Община Серого Дыхания (культ дыма) — три концепт-модели сектантов в белом: MPFB2 (MakeHuman для Blender) + одежда.
# Запуск (Blender как модуль bpy):
#   python build_cult.py <папка mpfb (boot.py, mpfb2, mh)> <папка вывода> [--quick] [--only=sister|brother|elder] [--no-group]
# Основа — build_farah.py (тело MPFB2, скелет Mixamo, глаза MakeHuman, кожа Валентины, одежда из копий тела).
# Новое: юбки и полы — «токарные» оболочки от кольца талии вниз (по профилю тела, с расклёшем и складками,
# с обходом рук в позе), коса, борода, капюшон, верёвочный пояс, сандалии, кадило, посох, пепельные мазки
# на лице (атрибут цвета вершин тела, не зависит от UV), дымка (объём) в сером «городском» свете.
import sys, os, math, random
MPFB_DIR, OUT = sys.argv[1], sys.argv[2]
QUICK = "--quick" in sys.argv
ONLY = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--only=")), None)
NO_GROUP = "--no-group" in sys.argv or ONLY is not None
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
random.seed(7)


def age_w(years):                                   # шкала MakeHuman: 0.5 = 25 лет, 1.0 = 90
	return 0.5 + (years - 25) / (90 - 25) * 0.5


# ------------------------------------------------------------------------------------------------------
# Персонажи
# ------------------------------------------------------------------------------------------------------
MEMBERS = [
	{"id": "sister", "label": "Сестра дыма", "x": -0.95, "rz": 14,
		"macro": {"gender": 0.0, "age": age_w(30), "muscle": 0.38, "weight": 0.36, "proportions": 0.62, "height": 0.52,
			"cupsize": 0.45, "firmness": 0.55, "race": {"caucasian": 0.9, "african": 0.03, "asian": 0.07}},
		"face": {"head/head-oval": 0.55, "nose/nose-scale-horiz-decr": 0.25, "nose/nose-point-up": 0.2, "nose/nose-width2-decr": 0.2,
			"cheek/l-cheek-bones-incr": 0.45, "cheek/r-cheek-bones-incr": 0.45, "cheek/l-cheek-volume-decr": 0.4, "cheek/r-cheek-volume-decr": 0.4,
			"chin/chin-width-decr": 0.3, "chin/chin-height-incr": 0.15, "mouth/mouth-lowerlip-volume-incr": 0.25,
			"mouth/mouth-upperlip-volume-incr": 0.15, "neck/neck-scale-horiz-decr": 0.3,
			"eyes/l-eye-height2-decr": 0.1, "eyes/r-eye-height2-decr": 0.1, "eyes/l-eye-eyefold-down": 0.15, "eyes/r-eye-eyefold-down": 0.15,
			"forehead/forehead-scale-vert-incr": 0.15, "mouth/mouth-angles-down": 0.1},
		# кожа: светлая, немного бледная
		"skin": {"hue": 0.5, "sat": 0.92, "val": 0.86, "tint": (0.92, 0.76, 0.66), "tf": 0.45},
		"hair": {"base": (0.02, 0.014, 0.011), "streak": (0.06, 0.04, 0.03), "thr": 0.55},
		"brow": (0.03, 0.022, 0.018), "ash": 0.55, "ash_style": "marks",
		"cloth": (0.86, 0.84, 0.78), "dirt": 0.22},
	{"id": "brother", "label": "Брат дыма", "x": 0.95, "rz": -14,
		"macro": {"gender": 1.0, "age": age_w(45), "muscle": 0.55, "weight": 0.66, "proportions": 0.45, "height": 0.55,
			"cupsize": 0.5, "firmness": 0.4, "race": {"caucasian": 0.85, "african": 0.05, "asian": 0.1}},
		"face": {"head/head-square": 0.45, "head/head-fat-incr": 0.3, "nose/nose-scale-horiz-incr": 0.3, "nose/nose-hump-incr": 0.35,
			"nose/nose-point-width-incr": 0.3, "nose/nose-flaring-incr": 0.2, "chin/chin-width-incr": 0.4, "chin/chin-jaw-drop-incr": 0.2,
			"eyebrows/eyebrows-trans-down": 0.35, "eyebrows/eyebrows-angle-down": 0.3, "eyes/l-eye-bag-incr": 0.4, "eyes/r-eye-bag-incr": 0.4,
			"eyes/l-eye-scale-decr": 0.15, "eyes/r-eye-scale-decr": 0.15, "head/head-age-incr": 0.5, "neck/neck-double-incr": 0.3,
			"mouth/mouth-upperlip-volume-decr": 0.3, "mouth/mouth-scale-horiz-incr": 0.1, "cheek/l-cheek-volume-incr": 0.25,
			"cheek/r-cheek-volume-incr": 0.25, "ears/l-ear-scale-incr": 0.2, "ears/r-ear-scale-incr": 0.2, "forehead/forehead-temple-decr": 0.3},
		# кожа: обветренная, смуглее
		"skin": {"hue": 0.5, "sat": 1.0, "val": 0.74, "tint": (0.82, 0.6, 0.47), "tf": 0.55},
		"hair": {"base": (0.03, 0.022, 0.016), "streak": (0.3, 0.29, 0.27), "thr": 0.66},
		"brow": (0.04, 0.03, 0.022), "ash": 0.75, "eye_hue": 0.47, "eye_sat": 0.8, "ash_style": "marks",
		"cloth": (0.84, 0.82, 0.75), "dirt": 0.32},
	{"id": "elder", "label": "Старейшина", "x": 0.0, "rz": 0, "y": 0.35,
		"macro": {"gender": 0.0, "age": age_w(66), "muscle": 0.32, "weight": 0.48, "proportions": 0.5, "height": 0.4,
			"cupsize": 0.5, "firmness": 0.15, "race": {"caucasian": 0.95, "african": 0.0, "asian": 0.05}},
		"face": {"head/head-age-incr": 0.8, "head/head-invertedtriangular": 0.35, "nose/nose-curve-convex": 0.35, "nose/nose-scale-vert-incr": 0.3,
			"nose/nose-point-down": 0.3, "cheek/l-cheek-volume-decr": 0.5, "cheek/r-cheek-volume-decr": 0.5, "cheek/l-cheek-trans-down": 0.35,
			"cheek/r-cheek-trans-down": 0.35, "mouth/mouth-angles-down": 0.35, "mouth/mouth-laugh-lines-in": 0.6,
			"mouth/mouth-lowerlip-volume-decr": 0.35, "mouth/mouth-upperlip-volume-decr": 0.4, "eyes/l-eye-bag-incr": 0.3, "eyes/r-eye-bag-incr": 0.3,
			"eyes/l-eye-height2-incr": 0.25, "eyes/r-eye-height2-incr": 0.25, "chin/chin-prominent-incr": 0.25, "neck/neck-scale-horiz-decr": 0.2,
			"forehead/forehead-temple-decr": 0.4, "eyebrows/eyebrows-angle-down": 0.2},
		# кожа: бледная, тонкая, старческая
		"skin": {"hue": 0.5, "sat": 0.78, "val": 0.84, "tint": (0.9, 0.76, 0.7), "tf": 0.4},
		"hair": {"base": (0.5, 0.49, 0.47), "streak": (0.72, 0.71, 0.69), "thr": 0.5},
		"brow": (0.42, 0.4, 0.38), "ash": 0.65, "eye_hue": 1.0, "eye_sat": 0.45, "eye_val": 0.85, "iris": 0.92, "ash_style": "rings",
		"cloth": (0.8, 0.79, 0.74), "dirt": 0.4},
]

# ------------------------------------------------------------------------------------------------------
# Общие помощники
# ------------------------------------------------------------------------------------------------------
ARM_B = {"mixamorig:%s%s" % (s, b) for s in ("Left", "Right") for b in
	("Arm", "ForeArm", "Hand", "HandIndex1", "HandIndex2", "HandIndex3", "HandMiddle1", "HandMiddle2", "HandMiddle3",
	"HandPinky1", "HandPinky2", "HandPinky3", "HandRing1", "HandRing2", "HandRing3", "HandThumb1", "HandThumb2", "HandThumb3")}
TORSO_B = {"mixamorig:Spine", "mixamorig:Spine1", "mixamorig:Spine2", "mixamorig:LeftShoulder", "mixamorig:RightShoulder"}
UPARM_B = {"mixamorig:LeftArm", "mixamorig:RightArm"}
FOREARM_B = {"mixamorig:LeftForeArm", "mixamorig:RightForeArm"}
LEG_B = {"mixamorig:Hips", "mixamorig:LeftUpLeg", "mixamorig:RightUpLeg", "mixamorig:LeftLeg", "mixamorig:RightLeg"}


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


def linen(name, base, dirt):
	"""Чуть грязный небелёный лён: альбедо ~0.85, шероховатость 0.8, ворс (sheen), пятна, серый налёт у подола, плетение."""
	m = bpy.data.materials.new(name)
	m.use_nodes = True
	nt = m.node_tree
	b = nt.nodes["Principled BSDF"]
	tc = nt.nodes.new("ShaderNodeTexCoord")
	nz = nt.nodes.new("ShaderNodeTexNoise")
	nz.inputs["Scale"].default_value = 3.5
	nz.inputs["Detail"].default_value = 8
	nz.inputs["Roughness"].default_value = 0.62
	nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
	rp = nt.nodes.new("ShaderNodeValToRGB")                       # пятна: где чище, где серее
	rp.color_ramp.elements[0].position = 0.38
	rp.color_ramp.elements[0].color = (1, 1, 1, 1)
	rp.color_ramp.elements[1].position = 0.75
	rp.color_ramp.elements[1].color = (0, 0, 0, 1)
	nt.links.new(nz.outputs["Fac"], rp.inputs[0])
	sep = nt.nodes.new("ShaderNodeSeparateXYZ")
	nt.links.new(tc.outputs["Object"], sep.inputs[0])
	hem = nt.nodes.new("ShaderNodeMapRange")                       # пепельный налёт снизу (подол по земле)
	hem.inputs["From Min"].default_value = 0.0
	hem.inputs["From Max"].default_value = 0.45
	hem.inputs["To Min"].default_value = 1.0
	hem.inputs["To Max"].default_value = 0.0
	nt.links.new(sep.outputs["Z"], hem.inputs["Value"])
	inv = nt.nodes.new("ShaderNodeMath")
	inv.operation = "SUBTRACT"
	inv.inputs[0].default_value = 1.0
	nt.links.new(rp.outputs["Color"], inv.inputs[1])
	add = nt.nodes.new("ShaderNodeMath")
	add.operation = "ADD"
	add.use_clamp = True
	nt.links.new(inv.outputs[0], add.inputs[0])
	nt.links.new(hem.outputs["Result"], add.inputs[1])
	mulf = nt.nodes.new("ShaderNodeMath")
	mulf.operation = "MULTIPLY"
	mulf.inputs[1].default_value = dirt
	nt.links.new(add.outputs[0], mulf.inputs[0])
	mix = nt.nodes.new("ShaderNodeMix")
	mix.data_type = "RGBA"
	mix.inputs[6].default_value = (*base, 1)
	mix.inputs[7].default_value = (base[0] * 0.55, base[1] * 0.55, base[2] * 0.53, 1)
	nt.links.new(mulf.outputs[0], mix.inputs["Factor"])
	nt.links.new(mix.outputs[2], b.inputs["Base Color"])
	b.inputs["Roughness"].default_value = 0.82
	b.inputs["Sheen Weight"].default_value = 0.6
	b.inputs["Sheen Roughness"].default_value = 0.45
	b.inputs["Sheen Tint"].default_value = (0.95, 0.95, 0.92, 1)
	b.inputs["Subsurface Weight"].default_value = 0.04
	b.inputs["Subsurface Radius"].default_value = (0.5, 0.5, 0.45)
	b.inputs["Subsurface Scale"].default_value = 0.004
	# плетение полотна: две частые волны крест-накрест + мелкий шум (неровная нить льна)
	w1 = nt.nodes.new("ShaderNodeTexWave")
	w1.bands_direction = "X"
	w1.inputs["Scale"].default_value = 420
	w2 = nt.nodes.new("ShaderNodeTexWave")
	w2.bands_direction = "Z"
	w2.inputs["Scale"].default_value = 420
	sl = nt.nodes.new("ShaderNodeTexNoise")
	sl.inputs["Scale"].default_value = 140
	for n_ in (w1, w2, sl):
		nt.links.new(tc.outputs["Object"], n_.inputs["Vector"])
	mx = nt.nodes.new("ShaderNodeMath")
	mx.operation = "MAXIMUM"
	nt.links.new(w1.outputs["Fac"], mx.inputs[0])
	nt.links.new(w2.outputs["Fac"], mx.inputs[1])
	ad2 = nt.nodes.new("ShaderNodeMath")
	ad2.operation = "ADD"
	nt.links.new(mx.outputs[0], ad2.inputs[0])
	nt.links.new(sl.outputs["Fac"], ad2.inputs[1])
	bp = nt.nodes.new("ShaderNodeBump")
	bp.inputs["Strength"].default_value = 0.12
	bp.inputs["Distance"].default_value = 0.0005
	nt.links.new(ad2.outputs[0], bp.inputs["Height"])
	nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
	return m


def rope_mat(name):
	m = bpy.data.materials.new(name)
	m.use_nodes = True
	nt = m.node_tree
	b = nt.nodes["Principled BSDF"]
	tc = nt.nodes.new("ShaderNodeTexCoord")
	wv = nt.nodes.new("ShaderNodeTexWave")
	wv.wave_type = "RINGS"
	wv.inputs["Scale"].default_value = 160
	wv.inputs["Distortion"].default_value = 3
	nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
	rp = nt.nodes.new("ShaderNodeValToRGB")
	rp.color_ramp.elements[0].color = (0.32, 0.27, 0.19, 1)
	rp.color_ramp.elements[1].color = (0.62, 0.55, 0.41, 1)
	nt.links.new(wv.outputs["Fac"], rp.inputs[0])
	nt.links.new(rp.outputs[0], b.inputs["Base Color"])
	b.inputs["Roughness"].default_value = 0.92
	b.inputs["Sheen Weight"].default_value = 0.8
	bp = nt.nodes.new("ShaderNodeBump")
	bp.inputs["Strength"].default_value = 0.6
	nt.links.new(wv.outputs["Fac"], bp.inputs["Height"])
	nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
	return m


def hair_mat(name, base, streak, thr):
	"""Волосы как в build_farah.py, но без лака: меньше блеска, сильнее рельеф прядей."""
	m = bpy.data.materials.new(name)
	m.use_nodes = True
	hn = m.node_tree
	hb = hn.nodes["Principled BSDF"]
	coord = hn.nodes.new("ShaderNodeTexCoord")
	wave = hn.nodes.new("ShaderNodeTexWave")
	wave.bands_direction = "Z"
	wave.inputs["Scale"].default_value = 300
	wave.inputs["Distortion"].default_value = 7
	wave.inputs["Detail"].default_value = 4
	hn.links.new(coord.outputs["Object"], wave.inputs["Vector"])
	streak_n = hn.nodes.new("ShaderNodeTexNoise")
	streak_n.inputs["Scale"].default_value = 40
	mp = hn.nodes.new("ShaderNodeMapping")
	mp.inputs["Scale"].default_value = (1, 1, 0.15)
	hn.links.new(coord.outputs["Object"], mp.inputs[0])
	hn.links.new(mp.outputs[0], streak_n.inputs["Vector"])
	ramp = hn.nodes.new("ShaderNodeValToRGB")
	ramp.color_ramp.elements[0].position = thr
	ramp.color_ramp.elements[0].color = (*base, 1)
	ramp.color_ramp.elements[1].position = thr + 0.1
	ramp.color_ramp.elements[1].color = (*streak, 1)
	hn.links.new(streak_n.outputs["Fac"], ramp.inputs[0])
	mixw = hn.nodes.new("ShaderNodeMix")                           # пряди чуть светлее/темнее
	mixw.data_type = "RGBA"
	mixw.blend_type = "MULTIPLY"
	mixw.inputs["Factor"].default_value = 0.35
	hn.links.new(ramp.outputs[0], mixw.inputs[6])
	hn.links.new(wave.outputs["Color"], mixw.inputs[7])
	hn.links.new(mixw.outputs[2], hb.inputs["Base Color"])
	hb.inputs["Roughness"].default_value = 0.62
	hb.inputs["Anisotropic"].default_value = 0.5
	hb.inputs["Sheen Weight"].default_value = 0.3
	hbump = hn.nodes.new("ShaderNodeBump")
	hbump.inputs["Strength"].default_value = 0.45
	hn.links.new(wave.outputs["Fac"], hbump.inputs["Height"])
	hn.links.new(hbump.outputs["Normal"], hb.inputs["Normal"])
	return m


def smooth_all(me):
	for p in me.polygons:
		p.use_smooth = True


def curve_obj(name, pts, radius, m, cyclic=False, res=6):
	cu = bpy.data.curves.new(name, "CURVE")
	cu.dimensions = "3D"
	cu.bevel_depth = radius
	cu.bevel_resolution = 3
	cu.resolution_u = res
	sp = cu.splines.new("NURBS" if not cyclic else "POLY")
	sp.points.add(len(pts) - 1)
	for i, p in enumerate(pts):
		sp.points[i].co = (p[0], p[1], p[2], 1)
	sp.use_cyclic_u = cyclic
	if not cyclic:
		sp.use_endpoint_u = True
		sp.order_u = 3
	o = bpy.data.objects.new(name, cu)
	bpy.context.collection.objects.link(o)
	cu.materials.append(m)
	return o


# --- 0. брови и ресницы — ассеты MakeHuman у Валентины (CC0), один импорт на всех -----------------------
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GAME + "valentina_standin.glb")
VAL_IMPORTED = set(bpy.data.objects) - before
VAL_EYE = next((o for o in VAL_IMPORTED if o.type == "MESH" and o.name.startswith("high-poly")), None)
VAL_BROW = next((o for o in VAL_IMPORTED if o.type == "MESH" and o.name.startswith("eyebrow")), None)
VAL_LASH = next((o for o in VAL_IMPORTED if o.type == "MESH" and o.name.startswith("eyelashes")), None)
for o in VAL_IMPORTED:
	o.hide_render = True
	o.hide_viewport = True


def center(o):
	pts = [o.matrix_world @ v.co for v in o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices]
	return sum(pts, Vector()) / len(pts), pts


# ------------------------------------------------------------------------------------------------------
# Сборка одного сектанта
# ------------------------------------------------------------------------------------------------------
def build_member(S):
	tag = S["id"]
	ID = tag.capitalize()
	coll = bpy.data.collections.new(ID)
	sc.collection.children.link(coll)
	bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[coll.name]
	print("[cult] ===", tag, flush=True)

	# --- 1. тело и лицо --------------------------------------------------------------------------------
	body = HumanService.create_human(macro_detail_dict=S["macro"])
	body.name = ID + "_Body"
	for rel, w in S["face"].items():
		p = os.path.join(TG, rel + ".target.gz")
		if os.path.exists(p):
			TargetService.load_target(body, p, weight=w)
		else:
			print("[cult] нет цели", rel)
	eyes = None
	try:
		eyes = HumanService.add_mhclo_asset(os.path.join(MPFB_DIR, "mh/makehuman/data/eyes/high-poly/high-poly.mhclo"), body,
			asset_type="Eyes", subdiv_levels=0, material_type="MAKESKIN")
	except Exception as e:
		print("[cult] глаза:", repr(e))
	rig = HumanService.add_builtin_rig(body, "mixamo")
	rig.name = ID + "_Rig"
	if eyes:
		eyes.name = ID + "_Eyes"
		for m_ in eyes.data.materials:                              # приглушить белки, оттенок радужки, влажный блеск
			en = m_.node_tree
			dt = en.nodes.get("diffuseTexture")
			di = en.nodes.get("diffuseIntensity")
			if dt and di:
				hs = en.nodes.new("ShaderNodeHueSaturation")
				hs.inputs["Hue"].default_value = S.get("eye_hue", 0.5)
				hs.inputs["Saturation"].default_value = S.get("eye_sat", 1.0)
				hs.inputs["Value"].default_value = S.get("eye_val", 0.62)
				en.links.new(dt.outputs["Color"], hs.inputs["Color"])
				en.links.new(hs.outputs["Color"], di.inputs["Color2"])
				# радужка крупнее: UV к центру зрачка своего острова (в brown_eye.png два глаза по диагонали)
				uvn = en.nodes.new("ShaderNodeTexCoord")
				spu = en.nodes.new("ShaderNodeSeparateXYZ")
				en.links.new(uvn.outputs["UV"], spu.inputs[0])
				suv = en.nodes.new("ShaderNodeMath")
				suv.operation = "ADD"
				en.links.new(spu.outputs["X"], suv.inputs[0])
				en.links.new(spu.outputs["Y"], suv.inputs[1])
				gt = en.nodes.new("ShaderNodeMath")
				gt.operation = "GREATER_THAN"
				gt.inputs[1].default_value = 1.0
				en.links.new(suv.outputs[0], gt.inputs[0])
				cm = en.nodes.new("ShaderNodeMix")
				cm.data_type = "VECTOR"
				cm.inputs[4].default_value = (0.2929, 0.2894, 0.0)
				cm.inputs[5].default_value = (0.7089, 0.7015, 0.0)
				en.links.new(gt.outputs[0], cm.inputs["Factor"])
				vs_ = en.nodes.new("ShaderNodeVectorMath")
				vs_.operation = "SUBTRACT"
				en.links.new(uvn.outputs["UV"], vs_.inputs[0])
				en.links.new(cm.outputs[1], vs_.inputs[1])
				vl = en.nodes.new("ShaderNodeVectorMath")             # только внутри острова глазного яблока (не роговица)
				vl.operation = "LENGTH"
				en.links.new(vs_.outputs[0], vl.inputs[0])
				lt = en.nodes.new("ShaderNodeMath")
				lt.operation = "LESS_THAN"
				lt.inputs[1].default_value = 0.28
				en.links.new(vl.outputs["Value"], lt.inputs[0])
				kf = en.nodes.new("ShaderNodeMath")
				kf.operation = "MULTIPLY_ADD"
				kf.inputs[1].default_value = S.get("iris", 0.8) - 1.0
				kf.inputs[2].default_value = 1.0
				en.links.new(lt.outputs[0], kf.inputs[0])
				vk = en.nodes.new("ShaderNodeVectorMath")
				vk.operation = "SCALE"
				en.links.new(kf.outputs[0], vk.inputs["Scale"])
				en.links.new(vs_.outputs[0], vk.inputs[0])
				va = en.nodes.new("ShaderNodeVectorMath")
				va.operation = "ADD"
				en.links.new(vk.outputs[0], va.inputs[0])
				en.links.new(cm.outputs[1], va.inputs[1])
				en.links.new(va.outputs[0], dt.inputs["Vector"])
			pb_ = en.nodes.get("Principled BSDF")
			if pb_:
				pb_.inputs["Roughness"].default_value = 0.12
				pb_.inputs["Coat Weight"].default_value = 0.6
	for o in (body, rig) + ((eyes,) if eyes else ()):
		for c in list(o.users_collection):
			if c != coll:
				c.objects.unlink(o)
		if coll not in o.users_collection:
			coll.objects.link(o)

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

	def eval_bm():
		dg = bpy.context.evaluated_depsgraph_get()
		ev = body.evaluated_get(dg)
		me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
		return me

	def eval_copy(name, keep_face, clip=None, cuts=()):
		"""Копия тела в позе покоя — грани, где keep_face истинно (и все вершины проходят clip); группы вершин сохраняются."""
		me = eval_bm()
		bm = bmesh.new()
		bm.from_mesh(me)
		dl = bm.verts.layers.deform.verify()
		drop = [f for f in bm.faces if not (keep_face(f, dl) and (clip is None or all(clip(v.co) for v in f.verts)))]
		bmesh.ops.delete(bm, geom=drop, context="FACES")
		for (pco, pno) in cuts:                                     # ровный край (вырез ворота и т.п.): срез плоскостью
			bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-5,
				plane_co=pco, plane_no=pno, clear_outer=True)
		bm.to_mesh(me)
		bm.free()
		o = bpy.data.objects.new(name, me)
		bpy.context.collection.objects.link(o)
		for g in body.vertex_groups:
			o.vertex_groups.new(name=g.name)
		return o

	def bone_set_face(bones, need_all=True):
		def f(face, dl):
			ok = [in_body(v, dl) and dominant(v, dl) in bones for v in face.verts]
			return all(ok) if need_all else any(ok) and all(in_body(v, dl) for v in face.verts)
		return f

	def inflate(o, off, thick, m, smooth=1, laplace=0):
		me = o.data
		me.update()
		for v in me.vertices:
			v.co += v.normal * off
		if laplace:
			sm = o.modifiers.new("Relax", "SMOOTH")
			sm.factor = 0.8
			sm.iterations = laplace
		sol = o.modifiers.new("Thick", "SOLIDIFY")
		sol.thickness = thick
		sol.offset = 1.0
		arm = o.modifiers.new("Armature", "ARMATURE")
		arm.object = rig
		if smooth:
			sub = o.modifiers.new("Smooth", "SUBSURF")
			sub.levels = smooth
			sub.render_levels = smooth
		me.materials.clear()
		me.materials.append(m)
		smooth_all(me)
		o.parent = rig
		return o

	def parent_bone(o, bone):
		bpy.context.view_layer.update()
		mw = o.matrix_world.copy()
		o.parent = rig
		o.parent_type = "BONE"
		o.parent_bone = bone
		o.matrix_world = mw

	# скрытие кожи под плотной одеждой (чтобы не просвечивала в локтях/подмышках): маска по вершинам
	hide_idx = set()

	def hide_under(keep_face, clip=None, shrink=2):
		me = eval_bm()
		bm = bmesh.new()
		bm.from_mesh(me)
		bm.verts.ensure_lookup_table()
		dl = bm.verts.layers.deform.verify()
		keepf = {f.index for f in bm.faces if keep_face(f, dl) and (clip is None or all(clip(v.co) for v in f.verts))}
		inside = {v.index for v in bm.verts if v.link_faces and all(f.index in keepf for f in v.link_faces)}
		for _ in range(shrink):
			inside = {i for i in inside if all(e.other_vert(bm.verts[i]).index in inside for e in bm.verts[i].link_edges)}
		# индексы в вычисленной сетке (без вершин-помощников) -> исходные индексы: по совпадению координат с маской MPFB
		bm.free()
		bpy.data.meshes.remove(me)
		return inside

	# соответствие индексов: вычисленная сетка = исходная без helper-вершин (маска сохраняет порядок)
	bgi = GI["body"]
	orig_ids = [v.index for v in body.data.vertices if any(g.group == bgi and g.weight > 0.0 for g in v.groups)]

	# --- 2. профиль тела (поза покоя): точки торса и ног без рук ----------------------------------------
	me = eval_bm()
	bm = bmesh.new()
	bm.from_mesh(me)
	dl = bm.verts.layers.deform.verify()
	samples = []
	for v in bm.verts:
		if in_body(v, dl):
			samples.append((v.co.copy(), dominant(v, dl)))
	lips = [v.co.copy() for v in bm.verts if v[dl].get(GI["lips"], 0.0) > 0.4]
	ears = [v.co.copy() for v in bm.verts if v[dl].get(GI["ears"], 0.0) > 0.5]
	scalp = [v.co.copy() for v in bm.verts if v[dl].get(GI["scalp"], 0.0) > 0.3]
	bm.free()
	bpy.data.meshes.remove(me)
	bverts = [p for p, _ in samples]
	H = max(p.z for p in bverts)
	core = [p for p, b in samples if b not in ARM_B]

	def front_y(z, half_w=0.17, dz=0.02):
		ys = [p.y for p in core if abs(p.z - z) < dz and abs(p.x) < half_w]
		return min(ys) if ys else -0.12

	def back_y(z, half_w=0.05, dz=0.02):
		ys = [p.y for p in core if abs(p.z - z) < dz and abs(p.x) < half_w]
		return max(ys) if ys else 0.1

	# лицо: кончик носа, глаза, губы, уши
	head_pts = [p for p in core if p.z > H * 0.86]
	nose = min((p for p in head_pts if abs(p.x) < 0.012), key=lambda p: p.y)
	if eyes:
		ec, ep = center(eyes)
		eye_z = ec.z
		eye_dx = (max(p.x for p in ep) - min(p.x for p in ep)) / 2 * 0.62
	else:
		eye_z, eye_dx = nose.z + 0.035, 0.032
	mouth_z = sum(p.z for p in lips) / len(lips)
	mouth_w = max(abs(p.x) for p in lips)
	lips_top, lips_bot = max(p.z for p in lips), min(p.z for p in lips)
	chin_pts = [p for p in core if abs(p.x) < 0.012 and lips_bot - 0.07 < p.z < lips_bot and p.y < nose.y + 0.06]
	chin_z = min(p.z for p in chin_pts) if chin_pts else mouth_z - 0.05
	# нижняя точка подбородка: самая нижняя точка лица впереди шеи
	under = [p for p in core if abs(p.x) < 0.03 and p.y < nose.y + 0.05 and mouth_z - 0.09 < p.z < mouth_z - 0.02]
	chin_z = min(p.z for p in under) if under else chin_z
	ear_front = min(p.y for p in ears) if ears else nose.y + 0.08
	head_c = Vector((0, sum(p.y for p in scalp) / len(scalp), eye_z))
	print("[cult] %s H=%.3f nose=(%.3f,%.3f) eye_z=%.3f mouth_z=%.3f chin_z=%.3f ear_front=%.3f" % (tag, H, nose.y, nose.z, eye_z, mouth_z, chin_z, ear_front), flush=True)

	# --- 3. кожа + пепельные мазки (атрибут цвета вершин «ash») -----------------------------------------
	sk = S["skin"]
	skin = bpy.data.materials.new(ID + "_Skin")
	skin.use_nodes = True
	nt = skin.node_tree
	bsdf = nt.nodes["Principled BSDF"]
	tex = nt.nodes.new("ShaderNodeTexImage")
	tex.image = bpy.data.images.load(GAME + "valentina_standin_valentina_skin_4k.png", check_existing=True)
	hsv = nt.nodes.new("ShaderNodeHueSaturation")
	hsv.inputs["Hue"].default_value = sk["hue"]
	hsv.inputs["Saturation"].default_value = sk["sat"]
	hsv.inputs["Value"].default_value = sk["val"]
	nt.links.new(tex.outputs["Color"], hsv.inputs["Color"])
	tint = nt.nodes.new("ShaderNodeMix")
	tint.data_type = "RGBA"
	tint.blend_type = "MULTIPLY"
	tint.inputs["Factor"].default_value = sk["tf"]
	tint.inputs[7].default_value = (*sk["tint"], 1)
	nt.links.new(hsv.outputs["Color"], tint.inputs[6])
	attr = nt.nodes.new("ShaderNodeAttribute")
	attr.attribute_name = "ash"
	tco = nt.nodes.new("ShaderNodeTexCoord")
	an = nt.nodes.new("ShaderNodeTexNoise")                        # рваные края мазка, растёртая зола
	an.inputs["Scale"].default_value = 140
	an.inputs["Detail"].default_value = 6
	an.inputs["Roughness"].default_value = 0.7
	nt.links.new(tco.outputs["Object"], an.inputs["Vector"])
	am = nt.nodes.new("ShaderNodeMath")
	am.operation = "MULTIPLY"
	nt.links.new(attr.outputs["Fac"], am.inputs[0])
	an2 = nt.nodes.new("ShaderNodeMapRange")
	an2.inputs["From Min"].default_value = 0.25
	an2.inputs["From Max"].default_value = 0.55
	nt.links.new(an.outputs["Fac"], an2.inputs["Value"])
	nt.links.new(an2.outputs["Result"], am.inputs[1])
	am2 = nt.nodes.new("ShaderNodeMath")
	am2.operation = "MULTIPLY"
	am2.use_clamp = True
	am2.inputs[1].default_value = S["ash"]
	nt.links.new(am.outputs[0], am2.inputs[0])
	ash_mix = nt.nodes.new("ShaderNodeMix")
	ash_mix.data_type = "RGBA"
	ash_mix.inputs[7].default_value = (0.09, 0.09, 0.09, 1)
	nt.links.new(am2.outputs[0], ash_mix.inputs["Factor"])
	nt.links.new(tint.outputs[2], ash_mix.inputs[6])
	nt.links.new(ash_mix.outputs[2], bsdf.inputs["Base Color"])
	rr = nt.nodes.new("ShaderNodeMapRange")                       # зола матовая
	rr.inputs["To Min"].default_value = 0.5
	rr.inputs["To Max"].default_value = 0.85
	nt.links.new(am2.outputs[0], rr.inputs["Value"])
	nt.links.new(rr.outputs["Result"], bsdf.inputs["Roughness"])
	bsdf.inputs["Subsurface Weight"].default_value = 0.12
	bsdf.inputs["Subsurface Radius"].default_value = (0.9, 0.45, 0.25)
	bsdf.inputs["Subsurface Scale"].default_value = 0.01
	pores = nt.nodes.new("ShaderNodeTexNoise")
	pores.inputs["Scale"].default_value = 900
	pores.inputs["Detail"].default_value = 4
	bump = nt.nodes.new("ShaderNodeBump")
	bump.inputs["Strength"].default_value = 0.1 if tag == "sister" else 0.16
	bump.inputs["Distance"].default_value = 0.0006
	nt.links.new(pores.outputs["Fac"], bump.inputs["Height"])
	nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
	body.data.materials.clear()
	body.data.materials.append(skin)
	smooth_all(body.data)

	# мазки: эллипсы в проекции на фронтальную плоскость (x, z), только спереди лица
	def strokes():
		st = S["ash_style"]
		fz = eye_z + 0.05                                           # лоб
		L = []
		if st == "marks":
			L.append((0.0, fz, 0.032, 0.009, 0.0, 1.0))                # мазок большим пальцем поперёк лба
			for sx in (1, -1):                                       # по два мазка пальцами на скулах
				for k in range(2):
					L.append((sx * (eye_dx + 0.004 + 0.008 * k), eye_z - 0.03 - 0.012 * k, 0.022, 0.0055, sx * math.radians(-18), 0.85))
		else:                                                        # старейшина: серые разводы вокруг глаз и рта
			for sx in (1, -1):
				L.append((sx * eye_dx, eye_z - 0.004, 0.026, 0.018, 0.0, 0.7))
			L.append((0.0, mouth_z - 0.004, mouth_w + 0.014, 0.02, 0.0, 0.55))
			L.append((0.0, fz + 0.006, 0.03, 0.008, 0.0, 0.8))
			L.append((0.0, chin_z + 0.012, 0.012, 0.022, 0.0, 0.6))     # вертикальная черта на подбородке
		return L

	SL = strokes()
	mods = [(m_, m_.show_viewport) for m_ in body.modifiers]
	for m_, _ in mods:
		m_.show_viewport = False
	dg = bpy.context.evaluated_depsgraph_get()
	full = body.evaluated_get(dg).data
	ca = body.data.color_attributes.new("ash", "FLOAT_COLOR", "POINT")
	for i, v in enumerate(full.vertices):
		p = v.co
		a = 0.0
		if p.z > H * 0.85 and p.y < nose.y + 0.075:
			for (cx, cz, ra, rb, ang, s_) in SL:
				dx, dz = p.x - cx, p.z - cz
				u = dx * math.cos(ang) + dz * math.sin(ang)
				w = -dx * math.sin(ang) + dz * math.cos(ang)
				a = max(a, s_ * math.exp(-((u / ra) ** 2 + (w / rb) ** 2) ** 1.6))
		ca.data[i].color = (a, a, a, 1)
	for m_, s in mods:
		m_.show_viewport = s

	# --- 4. помощники одежды --------------------------------------------------------------------------
	waist_pts = []

	def lathe(name, z_top, z_bot, offset, flare, folds, m, segs=96, rows=40, arms=None, hem_wave=0.008, extra_back=0.0):
		"""Оболочка вращения от кольца z_top вниз до z_bot: радиус по профилю тела (не меньше, чем выше — ткань не облегает
		ноги), плюс расклёш flare*t^1.4 и складки; подстраивается под руки в позе (не проходит сквозь кисти)."""
		zc = [p for p, b in samples if b not in ARM_B and abs(p.z - z_top) < 0.03]
		cy = (min(p.y for p in zc) + max(p.y for p in zc)) / 2
		N = segs
		prev = [0.0] * N
		ring = []
		ph = [random.uniform(0, 6.28) for _ in range(3)]
		for r in range(rows + 1):
			t = r / rows
			z = z_top + (z_bot - z_top) * t
			pts = [p for p in core if abs(p.z - z) < 0.018]
			rb = [None] * N
			for p in pts:
				a = math.atan2(p.y - cy, p.x)
				k = int((a % (2 * math.pi)) / (2 * math.pi) * N) % N
				d = math.hypot(p.x, p.y - cy)
				if rb[k] is None or d > rb[k]:
					rb[k] = d
			known = [k for k in range(N) if rb[k] is not None]
			if not known:
				rb = [prev[k] for k in range(N)]
			else:
				for k in range(N):
					if rb[k] is None:
						lo = max((j for j in known if j < k), default=known[-1] - N)
						hi = min((j for j in known if j > k), default=known[0] + N)
						f = (k - lo) / (hi - lo) if hi != lo else 0
						rb[k] = rb[lo % N] * (1 - f) + rb[hi % N] * f
			rb = [max(rb[(k + j) % N] for j in range(-3, 4)) for k in range(N)]
			rb = [sum(rb[(k + j) % N] for j in range(-3, 4)) / 7 for k in range(N)]
			cur = [max(rb[k] + offset, prev[k]) for k in range(N)]
			prev = cur
			row = []
			for k in range(N):
				a = (k + 0.5) / N * 2 * math.pi
				back = max(0.0, math.sin(a))                         # чуть больше ткани сзади
				fl = flare * t ** 1.4 * (1 + extra_back * back)
				fo = folds * (0.1 + 1.3 * t) * (math.sin(9 * a + ph[0]) * 0.6 + math.sin(14 * a + ph[1]) * 0.3 + math.sin(23 * a + ph[2]) * 0.15)
				rr_ = cur[k] + fl + fo
				zz = z + (hem_wave * math.sin(5 * a + ph[1]) if r == rows else 0.0)
				row.append([a, rr_, zz])
			ring.append(row)
		for _ in range(4):                                           # сгладить ступеньки профиля по вертикали
			for r in range(1, rows):
				for k in range(N):
					ring[r][k][1] = ring[r][k][1] * 0.5 + (ring[r - 1][k][1] + ring[r + 1][k][1]) * 0.25
		if arms:                                                     # обход кистей: вдавить радиус перед рукой
			for row in ring:
				z = row[0][2]
				near = [p for p in arms if abs(p.z - z) < 0.035]
				for p in near:
					ra = math.hypot(p.x, p.y - cy)
					aa = math.atan2(p.y - cy, p.x) % (2 * math.pi)
					for v in row:
						da = abs((v[0] - aa + math.pi) % (2 * math.pi) - math.pi)
						if da < 0.5:
							lim = ra - 0.022 - 0.0
							fall = math.cos(da / 0.5 * math.pi / 2) ** 2
							if v[1] > lim:
								v[1] = v[1] * (1 - fall) + max(lim, v[1] - 0.06) * fall
			for _ in range(3):
				for row in ring:
					rs = [v[1] for v in row]
					for k in range(N):
						row[k][1] = (rs[k - 1] + 2 * rs[k] + rs[(k + 1) % N]) / 4
		bm = bmesh.new()
		vs = [[bm.verts.new((v[1] * math.cos(v[0]), cy + v[1] * math.sin(v[0]), v[2])) for v in row] for row in ring]
		for r in range(rows):
			for k in range(N):
				bm.faces.new((vs[r][k], vs[r][(k + 1) % N], vs[r + 1][(k + 1) % N], vs[r + 1][k]))
		bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
		me = bpy.data.meshes.new(name)
		bm.to_mesh(me)
		bm.free()
		o = bpy.data.objects.new(name, me)
		bpy.context.collection.objects.link(o)
		me.materials.append(m)
		smooth_all(me)
		s_ = o.modifiers.new("Thick", "SOLIDIFY")
		s_.thickness = 0.004
		s_.offset = -1.0
		ss_ = o.modifiers.new("Smooth", "SUBSURF")
		ss_.levels = 1
		ss_.render_levels = 2
		parent_bone(o, "mixamorig:Hips")
		waist_pts.append((z_top, cy, [(v[0], v[1]) for v in ring[0]]))
		return o, cy, ring

	def rope_belt(z, cy, top_ring, rope, ends_side=1):
		pts = []
		for a, r in top_ring[::2]:
			pts.append((r * math.cos(a) * 1.02 + 0.0, cy + (r + 0.006) * math.sin(a) * 1.0, z))
		pts = [(x * (1 + 0.006 / max(0.05, math.hypot(x, y - cy))), y, z_) for x, y, z_ in pts]
		belt = curve_obj(ID + "_RopeBelt", pts, 0.0065, rope, cyclic=True)
		parent_bone(belt, "mixamorig:Hips")
		# узел и два свисающих конца спереди сбоку
		a0 = -math.pi / 2 + ends_side * 0.55
		r0 = min(top_ring, key=lambda q: abs((q[0] - (a0 % (2 * math.pi)) + math.pi) % (2 * math.pi) - math.pi))[1] + 0.012
		kx, ky = r0 * math.cos(a0), cy + r0 * math.sin(a0)
		bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=0.014, location=(kx, ky, z))
		knot = bpy.context.object
		knot.name = ID + "_RopeKnot"
		knot.scale = (1.0, 0.8, 0.9)
		knot.data.materials.append(rope)
		bpy.ops.object.shade_smooth()
		parent_bone(knot, "mixamorig:Hips")
		for j, (dx, ln) in enumerate(((-0.012, 0.3), (0.014, 0.24))):
			cp = [(kx + dx * t + 0.004 * math.sin(t * 7 + j), ky - 0.012 - 0.03 * t, z - ln * t) for t in (0, 0.25, 0.5, 0.75, 1.0)]
			end = curve_obj(ID + "_RopeEnd%d" % j, cp, 0.0055, rope)
			parent_bone(end, "mixamorig:Hips")
			bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.009, location=cp[-1])
			k2 = bpy.context.object
			k2.data.materials.append(rope)
			bpy.ops.object.shade_smooth()
			parent_bone(k2, "mixamorig:Hips")
		return kx, ky

	def sandals(m_sole, m_strap):
		for side in ("Left", "Right"):
			fb = {"mixamorig:%sFoot" % side, "mixamorig:%sToeBase" % side}
			fp = [p for p, b in samples if b in fb]
			if not fp:
				continue
			x0, x1 = min(p.x for p in fp), max(p.x for p in fp)
			y0, y1 = min(p.y for p in fp), max(p.y for p in fp)
			zb = min(p.z for p in fp)
			bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, zb - 0.002))
			so = bpy.context.object
			so.name = ID + "_Sole_" + side
			so.scale = (x1 - x0 + 0.014, y1 - y0 + 0.016, 0.016)
			bv = so.modifiers.new("Bevel", "BEVEL")
			bv.width = 0.006
			bv.segments = 3
			ss = so.modifiers.new("Sub", "SUBSURF")
			ss.levels = 2
			so.data.materials.append(m_sole)
			bpy.ops.object.shade_smooth()
			parent_bone(so, "mixamorig:%sFoot" % side)
			L = y1 - y0
			for (ya, yb) in ((y0 + L * 0.22, y0 + L * 0.3), (y0 + L * 0.5, y0 + L * 0.58)):
				st = eval_copy(ID + "_Strap_" + side, bone_set_face(fb), clip=lambda c, ya=ya, yb=yb: ya - 0.004 < c.y < yb + 0.004 and c.z > zb + 0.006)
				inflate(st, 0.003, 0.003, m_strap, smooth=1)
			# ремешок вокруг щиколотки
			st = eval_copy(ID + "_AnkleStrap_" + side, bone_set_face({"mixamorig:%sLeg" % side, "mixamorig:%sFoot" % side}, need_all=False),
				clip=lambda c: 0.085 < c.z < 0.1)
			inflate(st, 0.003, 0.003, m_strap, smooth=1)

	def filter_pendant(m_metal, cord_mat, z_pend):
		"""Знак общины — пробитый фильтр противогаза (открытое кольцо) на шнурке."""
		yp = front_y(z_pend, 0.08) - 0.03
		bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.022, depth=0.022, location=(0, yp, z_pend), rotation=(math.radians(90), 0, 0))
		can = bpy.context.object
		can.name = ID + "_Filter"
		bv = can.modifiers.new("Bevel", "BEVEL")
		bv.width = 0.003
		bv.segments = 2
		can.data.materials.append(m_metal)
		parent_bone(can, "mixamorig:Spine2")
		bpy.ops.mesh.primitive_torus_add(major_radius=0.013, minor_radius=0.0028, location=(0, yp - 0.0115, z_pend), rotation=(math.radians(90), 0, 0))
		ring = bpy.context.object
		ring.name = ID + "_FilterRing"
		bm_ = bmesh.new()                                            # разрыв кольца — «открытое кольцо»
		bm_.from_mesh(ring.data)
		cut = [v for v in bm_.verts if v.co.x > 0.004 and v.co.y > 0.004]
		bmesh.ops.delete(bm_, geom=cut, context="VERTS")
		bm_.to_mesh(ring.data)
		bm_.free()
		ring.data.materials.append(mat("FilterRing_" + tag, (0.55, 0.12, 0.05), 0.5))
		bpy.ops.object.shade_smooth()
		parent_bone(ring, "mixamorig:Spine2")
		bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.0075, depth=0.004, location=(0, yp - 0.0115, z_pend), rotation=(math.radians(90), 0, 0))
		hole = bpy.context.object
		hole.data.materials.append(mat("FilterHole", (0.01, 0.01, 0.01), 0.9))
		parent_bone(hole, "mixamorig:Spine2")
		zt = z_pend + 0.03
		zn = H * 0.835
		pts = []
		for s in (-1, 1):
			pass
		ny = front_y(zn, 0.06)
		by = back_y(zn, 0.06)
		nx = max((abs(p.x) for p in core if abs(p.z - zn) < 0.01), default=0.06) + 0.004
		# шнурок: сзади шеи, по бокам, вниз к фильтру (V)
		path = [(0.0, by + 0.012, zn + 0.01), (-nx, (by + ny) / 2, zn - 0.005), (-nx * 0.85, ny - 0.002, zn - 0.035),
			(-0.012, yp - 0.006, zt), (0.012, yp - 0.006, zt), (nx * 0.85, ny - 0.002, zn - 0.035), (nx, (by + ny) / 2, zn - 0.005), (0.0, by + 0.012, zn + 0.01)]
		cord = curve_obj(ID + "_FilterCord", path, 0.0016, cord_mat, cyclic=False)
		parent_bone(cord, "mixamorig:Spine2")

	# --- 5. одежда по типу ----------------------------------------------------------------------------
	CLOTH = linen(ID + "_Linen", S["cloth"], S["dirt"])
	ROPE = rope_mat(ID + "_Rope")
	z_neck = H * 0.84
	ncy = (front_y(z_neck, 0.06) + back_y(z_neck, 0.06)) / 2
	parts = {}

	def neck_cut(zc, k):
		"""Плоскость выреза: сзади выше, спереди ниже на k*dy; возвращает (срез, проверку для маски кожи)."""
		pno = Vector((0, -k, 1)).normalized()
		pco = Vector((0, ncy, zc))
		return [(pco, pno)], (lambda co: (co - pco).dot(pno) < -0.012)

	if tag == "sister":
		# лиф с длинными рукавами (по весам костей), вырез-лодочка
		bodice_keep = bone_set_face(TORSO_B | UPARM_B | FOREARM_B | {"mixamorig:Neck"}, need_all=False)
		cut, clip = neck_cut(H * 0.842, 0.8)
		parts["bodice"] = inflate(eval_copy(ID + "_Bodice", bodice_keep, None, cut), 0.005, 0.003, CLOTH)
		hide_idx |= hide_under(bodice_keep, clip)
	elif tag == "brother":
		bodice_keep = bone_set_face(TORSO_B | UPARM_B | FOREARM_B | {"mixamorig:Neck"}, need_all=False)
		cut, clip = neck_cut(H * 0.856, 0.6)
		parts["bodice"] = inflate(eval_copy(ID + "_TunicTop", bodice_keep, None, cut), 0.008, 0.003, CLOTH, laplace=2)
		hide_idx |= hide_under(bodice_keep, clip)
		legs_keep = bone_set_face(LEG_B)
		TROUS = linen(ID + "_LinenTrousers", tuple(c * 0.97 for c in S["cloth"]), S["dirt"] + 0.15)
		parts["trousers"] = inflate(eval_copy(ID + "_Trousers", legs_keep, lambda c: c.z > 0.105), 0.026, 0.003, TROUS, laplace=6)
		hide_idx |= hide_under(legs_keep, lambda c: c.z > 0.105)
	else:
		bodice_keep = bone_set_face(TORSO_B | UPARM_B | FOREARM_B | {"mixamorig:Neck"}, need_all=False)
		parts["bodice"] = inflate(eval_copy(ID + "_RobeTop", bodice_keep, lambda c: c.z < H * 0.865), 0.016, 0.004, CLOTH, laplace=8)
		hide_idx |= hide_under(bone_set_face(TORSO_B | UPARM_B | FOREARM_B), None)

	# нижний край лифа спереди = линия талии / пояса
	bodice = parts["bodice"]
	bz = [v.co.z for v in bodice.data.vertices if abs(v.co.x) < 0.06 and v.co.y < 0]
	z_waist = (min(bz) if bz else H * 0.58) + 0.035
	print("[cult] %s z_waist=%.3f" % (tag, z_waist), flush=True)

	# --- 6. волосы, борода, капюшон -------------------------------------------------------------------
	HAIR = hair_mat(ID + "_Hair", S["hair"]["base"], S["hair"]["streak"], S["hair"]["thr"])

	def scalp_face(face, dl):
		return all(v[dl].get(GI["scalp"], 0.0) > 0.3 for v in face.verts)

	cap_off = {"sister": 0.007, "brother": 0.003, "elder": 0.005}[tag]
	cap = inflate(eval_copy(ID + "_HairCap", scalp_face), cap_off, 0.004, HAIR, smooth=2)

	if tag == "sister":
		# коса, перекинутая через левое плечо на грудь: переплетённые доли (эллипсоиды), завязка и кисточка
		def fy_at(x, z, w=0.025):
			ys = [p.y for p in core if abs(p.x - x) < w and abs(p.z - z) < 0.02]
			return min(ys) if ys else front_y(z)

		def mid_at(x, z, w=0.02):
			ys = [p.y for p in core if abs(p.x - x) < w and abs(p.z - z) < 0.03]
			return ((min(ys) + max(ys)) / 2, max(p.z for p in core if abs(p.x - x) < w and p.z < H * 0.86)) if ys else (0.0, H * 0.8)

		sy, sz = mid_at(0.1, H * 0.81)
		sz = max(p.z for p in core if abs(p.x - 0.1) < 0.015 and abs(p.y - sy) < 0.03 and p.z < H * 0.86)
		hb_y = max(p.y for p in scalp if abs(p.z - (eye_z - 0.02)) < 0.03)
		ctrl = [Vector((0.03, hb_y - 0.005, eye_z - 0.01)), Vector((0.06, back_y(H * 0.85, 0.08) - 0.005, H * 0.85)),
			Vector((0.095, sy + 0.012, sz + 0.03)), Vector((0.1, fy_at(0.1, H * 0.77) - 0.028, H * 0.765)),
			Vector((0.095, fy_at(0.095, H * 0.7) - 0.03, H * 0.7)), Vector((0.09, fy_at(0.09, H * 0.635) - 0.028, H * 0.635))]

		def crom(P, t):
			n_ = len(P) - 1
			i = min(int(t * n_), n_ - 1)
			u = t * n_ - i
			p0, p1, p2, p3 = P[max(i - 1, 0)], P[i], P[i + 1], P[min(i + 2, n_)]
			return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u * u * u)

		n = 26
		cpts = [crom(ctrl, i / (n - 1)) for i in range(n)]
		from mathutils import Quaternion
		for i in range(n - 1):
			a, b_ = cpts[i], cpts[i + 1]
			tng = (b_ - a).normalized()
			q0 = tng.to_track_quat("Z", "Y")
			for side in (-1, 1):
				c_ = a.lerp(b_, 0.5 + 0.25 * side)
				side_v = q0 @ Vector((1, 0, 0))
				c_ = c_ + side_v * side * 0.008
				w_ = 0.024 * (1 - 0.35 * i / (n - 1))
				bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=1, location=c_)
				lobe = bpy.context.object
				lobe.name = ID + "_Braid"
				lobe.scale = (w_ * 0.72, w_ * 0.58, max((b_ - a).length * 0.85, w_ * 0.9))
				lobe.rotation_mode = "QUATERNION"
				lobe.rotation_quaternion = q0 @ Quaternion((0, 1, 0), side * math.radians(30))
				lobe.data.materials.append(HAIR)
				bpy.ops.object.shade_smooth()
				parent_bone(lobe, "mixamorig:Spine2" if c_.z < H * 0.84 else "mixamorig:Head")
		end = cpts[-1]
		bpy.ops.mesh.primitive_torus_add(major_radius=0.0095, minor_radius=0.0035, location=end, rotation=(0, 0, 0))
		tie = bpy.context.object
		tie.data.materials.append(ROPE)
		parent_bone(tie, "mixamorig:Spine2")
		bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.016, radius2=0.008, depth=0.06, location=end - Vector((0, 0, 0.032)), rotation=(math.radians(180), 0, 0))
		tuft = bpy.context.object
		tuft.data.materials.append(HAIR)
		sb = tuft.modifiers.new("Sub", "SUBSURF")
		sb.levels = 2
		bpy.ops.object.shade_smooth()
		parent_bone(tuft, "mixamorig:Spine2")
		# пряди от висков к затылку (объём над ушами)
		for sx in (1, -1):
			bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1, location=(sx * 0.062, head_c.y + 0.02, eye_z + 0.005))
			sw = bpy.context.object
			sw.scale = (0.022, 0.06, 0.035)
			sw.rotation_euler = (math.radians(-25), 0, 0)
			sw.data.materials.append(HAIR)
			bpy.ops.object.shade_smooth()
			shw = sw.modifiers.new("Hug", "SHRINKWRAP")
			shw.target = cap
			shw.wrap_mode = "OUTSIDE_SURFACE"
			shw.offset = 0.001
			parent_bone(sw, "mixamorig:Head")
	if tag == "brother":
		# короткая борода и усы: оболочка из копии кожи нижней части лица
		def beard_clip(c):
			if c.y > ear_front + 0.006 or c.z > nose.z - 0.01 or c.z < chin_z - 0.03:
				return False
			if abs(c.x) > 0.022 and c.z > nose.z - 0.026 and abs(c.x) < 0.05:
				return False                                           # крылья носа и щёки у носа чистые
			ax = abs(c.x)
			if c.z > mouth_z + 0.006 + 0.75 * max(0.0, ax - mouth_w) and ax > mouth_w + 0.004:
				return False                                           # линия щеки поднимается к бакенбардам
			if c.z < chin_z - 0.004 and c.y > nose.y + 0.09:
				return False                                           # под челюстью — только спереди шеи
			return True
		hb_keep = bone_set_face({"mixamorig:Head", "mixamorig:Neck"}, need_all=False)
		beard = eval_copy(ID + "_Beard", lambda f, dl: hb_keep(f, dl) and all(v[dl].get(GI["lips"], 0.0) < 0.05 for v in f.verts), beard_clip)
		# борода «соль с перцем»: частые светлые волоски по тёмно-русому, матовая, рельеф щетины
		BEARD = bpy.data.materials.new(ID + "_BeardMat")
		BEARD.use_nodes = True
		bn_ = BEARD.node_tree
		bb_ = bn_.nodes["Principled BSDF"]
		tcb = bn_.nodes.new("ShaderNodeTexCoord")
		st_ = bn_.nodes.new("ShaderNodeTexNoise")
		st_.inputs["Scale"].default_value = 900
		st_.inputs["Detail"].default_value = 2
		bn_.links.new(tcb.outputs["Object"], st_.inputs["Vector"])
		rb_ = bn_.nodes.new("ShaderNodeValToRGB")
		rb_.color_ramp.elements[0].position = 0.56
		rb_.color_ramp.elements[0].color = (0.05, 0.038, 0.03, 1)
		rb_.color_ramp.elements[1].position = 0.74
		rb_.color_ramp.elements[1].color = (0.4, 0.38, 0.35, 1)
		bn_.links.new(st_.outputs["Fac"], rb_.inputs[0])
		bn_.links.new(rb_.outputs[0], bb_.inputs["Base Color"])
		bb_.inputs["Roughness"].default_value = 0.95
		bb_.inputs["Specular IOR Level"].default_value = 0.2
		bb_.inputs["Sheen Weight"].default_value = 0.5
		bb_.inputs["Sheen Tint"].default_value = (0.6, 0.55, 0.5, 1)
		sb_ = bn_.nodes.new("ShaderNodeBump")
		sb_.inputs["Strength"].default_value = 0.7
		bn_.links.new(st_.outputs["Fac"], sb_.inputs["Height"])
		bn_.links.new(sb_.outputs["Normal"], bb_.inputs["Normal"])
		inflate(beard, 0.0018, 0.002, BEARD, smooth=2, laplace=2)
	if tag == "elder":
		# капюшон: копия головы и шеи без лица, раздута от центра головы, сглажена; свободный конец сзади
		yface = ear_front - 0.012
		zface = eye_z + 0.065
		def hood_clip(c):
			if c.z > zface or c.y > yface:
				return True
			return c.z < chin_z - 0.035 and c.y > nose.y + 0.05
		hood = eval_copy(ID + "_Hood", bone_set_face({"mixamorig:Head", "mixamorig:Neck", "mixamorig:Spine2", "mixamorig:LeftShoulder", "mixamorig:RightShoulder"}, need_all=False),
			hood_clip, [(Vector((0, 0, H * 0.772)), Vector((0, 0, -1)))])
		me_ = hood.data
		for v in me_.vertices:
			d = v.co - head_c
			back = max(0.0, (v.co.y - head_c.y) / 0.1)
			up = max(0.0, (v.co.z - eye_z) / 0.12)
			if v.co.z > H * 0.84:
				off = 0.03 + 0.018 * back + 0.008 * up
				v.co = v.co + d.normalized() * off
			else:                                                    # шея/плечи — свободно лежащий воротник
				nrm = Vector((v.co.x, v.co.y - ncy, 0))
				f = (H * 0.84 - v.co.z) / (H * 0.05)
				v.co = v.co + (nrm.normalized() if nrm.length > 1e-4 else Vector((0, 1, 0))) * (0.03 * (1 - min(1, f)) + 0.024)
		inflate(hood, 0.0, 0.006, CLOTH, smooth=2, laplace=30)
		parts["hood"] = hood

	# --- 7. брови и ресницы -----------------------------------------------------------------------------
	if VAL_EYE and eyes:
		dg2 = bpy.context.evaluated_depsgraph_get()
		vc, vp = center(VAL_EYE)
		fc, fp = center(eyes)
		vw = max(p.x for p in vp) - min(p.x for p in vp)
		fw = max(p.x for p in fp) - min(p.x for p in fp)
		k = fw / vw if vw > 0 else 1.0
		for src, nm in ((VAL_BROW, ID + "_Brows"), (VAL_LASH, ID + "_Lashes")):
			if not src or (tag == "elder" and nm.endswith("_Lashes")):    # у старейшины ресницы редкие — без ассета
				continue
			ev = src.evaluated_get(dg2)
			me = bpy.data.meshes.new_from_object(ev, depsgraph=dg2)
			me.transform(src.matrix_world)
			for v in me.vertices:
				v.co = fc + (v.co - vc) * k
			o = bpy.data.objects.new(nm, me)
			bpy.context.collection.objects.link(o)
			for m_ in src.data.materials:
				me.materials.append(m_)
			if nm.endswith("_Brows"):
				bm_ = bpy.data.materials.new(ID + "_BrowsMat")
				bm_.use_nodes = True
				bt = bm_.node_tree.nodes.new("ShaderNodeTexImage")
				bt.image = bpy.data.images.load(GAME + "valentina_standin_eyebrow001.png", check_existing=True)
				bp = bm_.node_tree.nodes["Principled BSDF"]
				bp.inputs["Base Color"].default_value = (*S["brow"], 1)
				bp.inputs["Roughness"].default_value = 0.65
				bm_.node_tree.links.new(bt.outputs["Alpha"], bp.inputs["Alpha"])
				me.materials.clear()
				me.materials.append(bm_)
				sw = o.modifiers.new("Hug", "SHRINKWRAP")
				sw.target = body
				sw.wrap_method = "NEAREST_SURFACEPOINT"
				sw.offset = 0.0012
				if tag == "brother":
					o.scale = (1.06, 1.0, 1.25)
			parent_bone(o, "mixamorig:Head")

	# --- 8. маска кожи под одеждой + сглаживание тела ---------------------------------------------------
	if hide_idx:
		vg = body.vertex_groups.new(name="cult_covered")
		ids = [orig_ids[i] for i in hide_idx if i < len(orig_ids)]
		vg.add(ids, 1.0, "REPLACE")
		mk = body.modifiers.new("HideCovered", "MASK")
		mk.vertex_group = "cult_covered"
		mk.invert_vertex_group = True
	sub = body.modifiers.new("Smooth", "SUBSURF")
	sub.levels = 1
	sub.render_levels = 2

	# глаза MPFB без модификатора скелета — привязать к кости головы, иначе при повороте головы веки «уезжают» с глаз
	if eyes:
		parent_bone(eyes, "mixamorig:Head")

	# --- 9. поза ----------------------------------------------------------------------------------------
	bpy.context.view_layer.objects.active = rig
	bpy.ops.object.mode_set(mode="POSE")

	def rot_world(bn, axis, ang):
		pb = rig.pose.bones[bn]
		head = pb.head.copy()
		M = Matrix.Translation(head) @ Matrix.Rotation(ang, 4, axis) @ Matrix.Translation(-head)
		pb.matrix = M @ pb.matrix
		bpy.context.view_layer.update()

	arm_down = {"sister": 30, "brother": 27, "elder": 28}[tag]
	rot_world("mixamorig:LeftArm", "Y", math.radians(arm_down))
	rot_world("mixamorig:RightArm", "Y", math.radians(-arm_down))
	if tag == "sister":                                            # ладони чуть вперёд, спокойная поза
		rot_world("mixamorig:LeftForeArm", "X", math.radians(-12))
		rot_world("mixamorig:RightForeArm", "X", math.radians(-12))
		rot_world("mixamorig:Head", "X", math.radians(-4))
	if tag == "brother":
		rot_world("mixamorig:LeftForeArm", "X", math.radians(-8))
		rot_world("mixamorig:RightForeArm", "X", math.radians(-8))
		rot_world("mixamorig:Head", "Z", math.radians(-4))
	if tag == "elder":                                             # правая рука держит посох (локоть согнут)
		rot_world("mixamorig:RightArm", "X", math.radians(-14))
		rot_world("mixamorig:RightForeArm", "X", math.radians(-62))
		rot_world("mixamorig:LeftForeArm", "X", math.radians(-10))
		rot_world("mixamorig:Head", "X", math.radians(5))
		rot_world("mixamorig:Spine1", "X", math.radians(3))
		pbh = rig.pose.bones["mixamorig:RightHand"]
		for fn in ("Index", "Middle", "Ring", "Pinky"):
			for j in (1, 2, 3):
				pb = rig.pose.bones["mixamorig:RightHand%s%d" % (fn, j)]
				pb.rotation_mode = "XYZ"
				pb.rotation_euler.x = math.radians(CURL_ANG[j - 1])
		for j, a in ((1, 15), (2, 30), (3, 30)):
			pb = rig.pose.bones["mixamorig:RightHandThumb%d" % j]
			pb.rotation_mode = "XYZ"
			pb.rotation_euler.z = math.radians(-a)
		bpy.context.view_layer.update()
	bpy.ops.object.mode_set(mode="OBJECT")
	bpy.context.view_layer.update()

	# точки рук в позе (для обхода юбкой)
	me = eval_bm()
	bm = bmesh.new()
	bm.from_mesh(me)
	dl = bm.verts.layers.deform.verify()
	arm_pts = [v.co.copy() for v in bm.verts if in_body(v, dl) and dominant(v, dl) in ARM_B and v.co.z < z_waist + 0.05]
	hand_pts = [v.co.copy() for v in bm.verts if in_body(v, dl) and dominant(v, dl) and "RightHand" in dominant(v, dl)]
	bm.free()
	bpy.data.meshes.remove(me)

	# --- 10. юбки/полы (токарные оболочки) и пояс ------------------------------------------------------
	knee_z = H * 0.285
	if tag == "sister":
		skirt, cy, ring = lathe(ID + "_Skirt", z_waist, 0.055, 0.012, 0.1, 0.016, CLOTH, arms=arm_pts, extra_back=0.3)
		rope_belt(z_waist - 0.012, cy, waist_pts[-1][2], ROPE, ends_side=-1)
	elif tag == "brother":
		skirt, cy, ring = lathe(ID + "_TunicSkirt", z_waist, knee_z - 0.02, 0.03, 0.07, 0.01, CLOTH, arms=arm_pts, extra_back=0.2)
		kx, ky = rope_belt(z_waist - 0.012, cy, waist_pts[-1][2], ROPE, ends_side=-1)
		# кадило из латуни на цепочках у левого бедра
		BRASS = mat("Brass_" + tag, (0.62, 0.45, 0.2), 0.32, 1.0)
		BRASSD = mat("BrassDark_" + tag, (0.25, 0.17, 0.08), 0.55, 1.0)
		a0 = -math.pi / 2 + 0.75
		r0 = min(waist_pts[-1][2], key=lambda q: abs((q[0] - (a0 % (2 * math.pi)) + math.pi) % (2 * math.pi) - math.pi))[1]
		hx, hy, hz = (r0 + 0.012) * math.cos(a0), cy + (r0 + 0.012) * math.sin(a0), z_waist - 0.012
		cz_ = hz - 0.2
		# точка подвеса чуть вперёд от ткани
		cyy = hy - 0.05
		cxx = hx + 0.01
		bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.04, location=(cxx, cyy, cz_))
		bowl = bpy.context.object
		bowl.name = ID + "_Censer"
		bowl.scale = (1, 1, 0.85)
		bowl.data.materials.append(BRASS)
		bpy.ops.object.shade_smooth()
		parent_bone(bowl, "mixamorig:Hips")
		for dz, rr_ in ((0.0, 0.0405), (0.012, 0.038)):
			bpy.ops.mesh.primitive_torus_add(major_radius=rr_, minor_radius=0.0025, location=(cxx, cyy, cz_ + dz))
			t_ = bpy.context.object
			t_.data.materials.append(BRASSD)
			parent_bone(t_, "mixamorig:Hips")
		bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.022, radius2=0.004, depth=0.03, location=(cxx, cyy, cz_ + 0.044))
		t_ = bpy.context.object
		t_.data.materials.append(BRASS)
		bpy.ops.object.shade_smooth()
		parent_bone(t_, "mixamorig:Hips")
		bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.016, depth=0.012, location=(cxx, cyy, cz_ - 0.036))
		t_ = bpy.context.object
		t_.data.materials.append(BRASSD)
		parent_bone(t_, "mixamorig:Hips")
		for k in range(8):                                       # отверстия-прорези крышки
			a = k / 8 * 2 * math.pi
			bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=6, radius=0.005, location=(cxx + 0.03 * math.cos(a), cyy + 0.03 * math.sin(a), cz_ + 0.024))
			h_ = bpy.context.object
			h_.data.materials.append(mat("Ember_" + tag, (0.02, 0.01, 0.005), 0.9, emit=(1.0, 0.35, 0.08), strength=0.4))
			parent_bone(h_, "mixamorig:Hips")
		CHAIN = mat("Chain_" + tag, (0.5, 0.38, 0.18), 0.35, 1.0)
		for k in range(3):
			a = k / 3 * 2 * math.pi + 0.3
			p0 = (cxx + 0.036 * math.cos(a), cyy + 0.036 * math.sin(a), cz_ + 0.01)
			ch = curve_obj(ID + "_CenserChain%d" % k, [p0, ((p0[0] + hx) / 2, (p0[1] + hy) / 2 - 0.01, (p0[2] + hz) / 2), (hx, hy - 0.008, hz - 0.01)], 0.0014, CHAIN)
			parent_bone(ch, "mixamorig:Hips")
		# тонкая струйка дыма над кадилом
		bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.035, depth=0.4, location=(cxx, cyy, cz_ + 0.25))
		wisp = bpy.context.object
		wisp.name = ID + "_CenserSmoke"
		wm = bpy.data.materials.new("CenserSmoke_" + tag)
		wm.use_nodes = True
		wn = wm.node_tree
		wn.nodes.remove(wn.nodes["Principled BSDF"])
		vol = wn.nodes.new("ShaderNodeVolumePrincipled")
		vol.inputs["Color"].default_value = (0.7, 0.7, 0.72, 1)
		tc_ = wn.nodes.new("ShaderNodeTexCoord")
		nz_ = wn.nodes.new("ShaderNodeTexNoise")
		nz_.inputs["Scale"].default_value = 9
		nz_.inputs["Detail"].default_value = 6
		wn.links.new(tc_.outputs["Object"], nz_.inputs["Vector"])
		gr = wn.nodes.new("ShaderNodeTexGradient")
		gr.gradient_type = "SPHERICAL"
		mpp = wn.nodes.new("ShaderNodeMapping")
		mpp.inputs["Scale"].default_value = (28, 28, 0.0)
		wn.links.new(tc_.outputs["Object"], mpp.inputs[0])
		wn.links.new(mpp.outputs[0], gr.inputs["Vector"])
		mm = wn.nodes.new("ShaderNodeMath")
		mm.operation = "MULTIPLY"
		wn.links.new(gr.outputs["Fac"], mm.inputs[0])
		rmp = wn.nodes.new("ShaderNodeMapRange")
		rmp.inputs["From Min"].default_value = 0.45
		rmp.inputs["From Max"].default_value = 0.75
		rmp.inputs["To Max"].default_value = 6.0
		wn.links.new(nz_.outputs["Fac"], rmp.inputs["Value"])
		wn.links.new(rmp.outputs["Result"], mm.inputs[1])
		wn.links.new(mm.outputs[0], vol.inputs["Density"])
		wn.links.new(vol.outputs[0], wn.nodes["Material Output"].inputs["Volume"])
		wisp.data.materials.append(wm)
		sdf = wisp.modifiers.new("Twist", "SIMPLE_DEFORM")
		sdf.deform_method = "TWIST"
		sdf.angle = math.radians(90)
		parent_bone(wisp, "mixamorig:Hips")
		SOLE = mat("Sole_" + tag, (0.16, 0.1, 0.06), 0.75)
		STRAP = mat("Strap_" + tag, (0.24, 0.15, 0.08), 0.6, sheen=0.2)
		sandals(SOLE, STRAP)
	else:
		skirt, cy, ring = lathe(ID + "_RobeSkirt", z_waist + 0.02, 0.035, 0.035, 0.11, 0.016, CLOTH, arms=arm_pts, extra_back=0.5)
		rope_belt(z_waist - 0.002, cy, waist_pts[-1][2], ROPE, ends_side=1)
		SOLE = mat("Sole_" + tag, (0.14, 0.09, 0.05), 0.75)
		STRAP = mat("Strap_" + tag, (0.2, 0.12, 0.07), 0.6, sheen=0.2)
		sandals(SOLE, STRAP)
		# посох: прямая палка через кулак правой руки
		if hand_pts:
			bpy.context.view_layer.update()
			pbh = rig.pose.bones["mixamorig:RightHand"]
			h0 = rig.matrix_world @ pbh.head
			m1 = rig.matrix_world @ rig.pose.bones["mixamorig:RightHandMiddle1"].head
			hc = h0.lerp(m1, 0.85)
			# сторона ладони: от центра тела наружу у правой руки — ладонь смотрит внутрь (+x)
			hc = hc + Vector((STAFF_OFF[0], STAFF_OFF[1], 0))
			top, bot = 1.62 if H > 1.55 else H * 1.0, 0.0
			WOOD = bpy.data.materials.new("Staff_Wood")
			WOOD.use_nodes = True
			wn = WOOD.node_tree
			wb = wn.nodes["Principled BSDF"]
			wt = wn.nodes.new("ShaderNodeTexWave")
			wt.bands_direction = "Z"
			wt.inputs["Scale"].default_value = 12
			wt.inputs["Distortion"].default_value = 14
			wt.inputs["Detail"].default_value = 6
			tcw = wn.nodes.new("ShaderNodeTexCoord")
			mpw = wn.nodes.new("ShaderNodeMapping")
			mpw.inputs["Scale"].default_value = (30, 30, 1.5)
			wn.links.new(tcw.outputs["Object"], mpw.inputs[0])
			wn.links.new(mpw.outputs[0], wt.inputs["Vector"])
			wr = wn.nodes.new("ShaderNodeValToRGB")
			wr.color_ramp.elements[0].color = (0.08, 0.05, 0.03, 1)
			wr.color_ramp.elements[1].color = (0.26, 0.17, 0.1, 1)
			wn.links.new(wt.outputs["Fac"], wr.inputs[0])
			wn.links.new(wr.outputs[0], wb.inputs["Base Color"])
			wb.inputs["Roughness"].default_value = 0.6
			wbp = wn.nodes.new("ShaderNodeBump")
			wbp.inputs["Strength"].default_value = 0.4
			wn.links.new(wt.outputs["Fac"], wbp.inputs["Height"])
			wn.links.new(wbp.outputs["Normal"], wb.inputs["Normal"])
			bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.016, depth=top - bot, location=(hc.x, hc.y, (top + bot) / 2))
			staff = bpy.context.object
			staff.name = ID + "_Staff"
			bm_ = bmesh.new()
			bm_.from_mesh(staff.data)
			for v in bm_.verts:                                      # лёгкий изгиб и сужение к низу
				t = (v.co.z + (top - bot) / 2) / (top - bot)
				v.co.x += 0.012 * math.sin(t * math.pi * 1.3)
				v.co.y += 0.008 * math.sin(t * math.pi * 2.1)
				sc_ = 0.8 + 0.2 * t
				v.co.x *= 1.0
				v.co.x = v.co.x * sc_ if abs(v.co.x) < 0.03 else v.co.x
			bm_.to_mesh(staff.data)
			bm_.free()
			staff.data.materials.append(WOOD)
			bpy.ops.object.shade_smooth()
			bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=0.024, location=(hc.x + 0.01, hc.y, top))
			knob = bpy.context.object
			knob.scale = (1, 1, 0.8)
			knob.data.materials.append(WOOD)
			bpy.ops.object.shade_smooth()
			# обмотка верёвкой под рукой
			for k in range(5):
				bpy.ops.mesh.primitive_torus_add(major_radius=0.0175, minor_radius=0.003, location=(hc.x, hc.y, hc.z - 0.07 - 0.008 * k))
				w_ = bpy.context.object
				w_.data.materials.append(ROPE)
				parent_bone(w_, "mixamorig:RightHand")
			parent_bone(staff, "mixamorig:RightHand")
			parent_bone(knob, "mixamorig:RightHand")

	filter_pendant(mat("FilterMetal_" + tag, (0.12, 0.13, 0.12), 0.55, 0.6), mat("Cord_" + tag, (0.1, 0.09, 0.08), 0.8), H * (0.735 if tag != "sister" else 0.745))

	objs = [o for o in coll.objects]
	return {"id": tag, "S": S, "rig": rig, "coll": coll, "H": H, "eye_z": eye_z, "body": body}


CURL_ANG = (55, 70, 55)                    # сгиб пальцев вокруг посоха (локальная X фаланг Mixamo)
STAFF_OFF = (0.012, -0.004)

built = []
for S in MEMBERS:
	if ONLY and S["id"] != ONLY:
		continue
	built.append(build_member(S))
for o in VAL_IMPORTED:
	bpy.data.objects.remove(o, do_unlink=True)

# ------------------------------------------------------------------------------------------------------
# Сцена: тусклый серый свет задымлённого города, лёгкая дымка, мокрый бетон
# ------------------------------------------------------------------------------------------------------
bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 20 if QUICK else 48
sc.cycles.use_denoising = True
sc.cycles.volume_bounces = 0
sc.cycles.max_bounces = 6
sc.render.resolution_percentage = 50 if QUICK else 100
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Medium High Contrast"
sc.view_settings.exposure = -0.75
sc.world = bpy.data.worlds.new("SmokyCity")
sc.world.use_nodes = True
wbg = sc.world.node_tree.nodes["Background"]
wbg.inputs["Color"].default_value = (0.03, 0.031, 0.034, 1)
wbg.inputs["Strength"].default_value = 1.0

FLOOR = bpy.data.materials.new("WetConcrete")
FLOOR.use_nodes = True
fn = FLOOR.node_tree
fb = fn.nodes["Principled BSDF"]
fnz = fn.nodes.new("ShaderNodeTexNoise")
fnz.inputs["Scale"].default_value = 6
fnz.inputs["Detail"].default_value = 10
frp = fn.nodes.new("ShaderNodeValToRGB")
frp.color_ramp.elements[0].color = (0.07, 0.07, 0.072, 1)
frp.color_ramp.elements[1].color = (0.17, 0.17, 0.17, 1)
fn.links.new(fnz.outputs["Fac"], frp.inputs[0])
fn.links.new(frp.outputs[0], fb.inputs["Base Color"])
frr = fn.nodes.new("ShaderNodeMapRange")
frr.inputs["To Min"].default_value = 0.35
frr.inputs["To Max"].default_value = 0.85
fn.links.new(fnz.outputs["Fac"], frr.inputs["Value"])
fn.links.new(frr.outputs["Result"], fb.inputs["Roughness"])
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
bpy.context.object.data.materials.append(FLOOR)
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 4.5, 5), rotation=(math.radians(90), 0, 0))
bpy.context.object.data.materials.append(mat("BackWall", (0.11, 0.115, 0.12), 0.9))

# дымка: куб с однородным рассеивающим объёмом (камера внутри)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -1.0, 2.5))
haze = bpy.context.object
haze.name = "Haze"
haze.scale = (14, 14, 5)
hm = bpy.data.materials.new("Haze")
hm.use_nodes = True
hn_ = hm.node_tree
hn_.nodes.remove(hn_.nodes["Principled BSDF"])
hv = hn_.nodes.new("ShaderNodeVolumeScatter")
hv.inputs["Color"].default_value = (0.8, 0.82, 0.85, 1)
hv.inputs["Density"].default_value = 0.028
hn_.links.new(hv.outputs[0], hn_.nodes["Material Output"].inputs["Volume"])
haze.data.materials.append(hm)
haze.visible_shadow = False


def light(loc, energy, color, size, target):
	ld = bpy.data.lights.new("L", "AREA")
	ld.energy = energy
	ld.color = color
	ld.size = size
	o = bpy.data.objects.new("L", ld)
	sc.collection.objects.link(o)
	o.location = loc
	o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
	return o


light((-1.8, -2.6, 3.2), 150, (0.86, 0.9, 0.98), 2.6, (0, 0, 1.1))       # ключ: рассеянный серый день сквозь дым
light((2.4, -1.8, 1.8), 40, (0.78, 0.82, 0.9), 3.0, (0, 0, 1.0))        # заполняющий
light((0.6, 2.4, 2.6), 170, (1.0, 0.82, 0.62), 1.2, (0, 0, 1.4))        # контровой: тёплый отсвет фонаря в дыму
light((0, -1.2, 4.8), 35, (0.85, 0.88, 0.95), 4.0, (0, 0, 0.8))        # небо сверху
FACE_FILL = light((0.25, -0.9, 1.5), 4.0, (0.9, 0.92, 1.0), 0.6, (0, 0, 1.45))   # мягкий фронтальный блик в глазах (только крупный план)
FACE_FILL.hide_render = True
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
	print("[cult] rendered", name, flush=True)


def place(B, x, y, rz):
	B["rig"].location = (x, y, 0)
	B["rig"].rotation_euler = (0, 0, math.radians(rz))


for B in built:
	for C in built:
		C["coll"].hide_render = C is not B
		C["coll"].hide_viewport = C is not B
	place(B, 0, 0, 0)
	bpy.context.view_layer.update()
	H, ez = B["H"], B["eye_z"]
	shoot("cult_%s_front" % B["id"], (0, -3.9, 0.98), (0, 0, 0.88), 50)
	shoot("cult_%s_34" % B["id"], (2.3, -3.0, 1.12), (0, 0, 0.9), 50)
	FACE_FILL.hide_render = False
	FACE_FILL.location = (0.25, -0.9, ez + 0.05)
	shoot("cult_%s_face" % B["id"], (0.3, -0.98, ez + 0.0), (0, 0, ez - 0.04), 85, (900, 900))
	FACE_FILL.hide_render = True

if not NO_GROUP:
	for B in built:
		B["coll"].hide_render = False
		B["coll"].hide_viewport = False
		S = B["S"]
		place(B, S["x"], S.get("y", 0.0), S["rz"])
	bpy.context.view_layer.update()
	shoot("cult_group", (0.0, -5.2, 1.1), (0, 0.1, 0.86), 46, (1600, 1150))

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "cult_%s.blend" % (ONLY or "all")), compress=True)
print("[cult] done", flush=True)
