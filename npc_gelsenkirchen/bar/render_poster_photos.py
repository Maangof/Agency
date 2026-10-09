# «Фото» для реалистичных постеров (рендер Blender): рекламный снимок пива и сцена с микрофоном в дыму.
# python render_poster_photos.py [--quick]  (Blender как модуль bpy) -> props_tex/photo_beer.png, photo_stage.png
import bpy, bmesh, math, os, sys, random
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, "props_tex")
QUICK = "--quick" in sys.argv
rnd = random.Random(7)


def reset():
	bpy.ops.wm.read_factory_settings(use_empty=True)
	sc = bpy.context.scene
	sc.render.engine = "CYCLES"
	sc.cycles.device = "CPU"
	sc.cycles.samples = 24 if QUICK else 96
	sc.cycles.use_denoising = True
	sc.render.resolution_x, sc.render.resolution_y = 1024, 1448
	sc.render.resolution_percentage = 50 if QUICK else 100
	sc.view_settings.view_transform = "AgX"
	sc.view_settings.look = "AgX - Medium High Contrast"
	return sc


def mat(name, color, rough=0.5, metal=0.0, trans=0.0, emit=None, strength=0.0, ior=1.5):
	m = bpy.data.materials.new(name)
	m.use_nodes = True
	b = m.node_tree.nodes["Principled BSDF"]
	b.inputs["Base Color"].default_value = (*color, 1)
	b.inputs["Roughness"].default_value = rough
	b.inputs["Metallic"].default_value = metal
	b.inputs["Transmission Weight"].default_value = trans
	b.inputs["IOR"].default_value = ior
	if emit:
		b.inputs["Emission Color"].default_value = (*emit, 1)
		b.inputs["Emission Strength"].default_value = strength
	return m


def lathe(name, prof, m, segs=64, loc=(0, 0, 0), band=None):
	"""prof — [(r, z)]; band=(r, z0, z1, material) — этикетка с развёрткой."""
	bm = bmesh.new()
	uv = bm.loops.layers.uv.new("UVMap")
	rings = [[bm.verts.new((r * math.cos(2 * math.pi * k / segs), r * math.sin(2 * math.pi * k / segs), z)) for k in range(segs)] for r, z in prof]
	for i in range(len(rings) - 1):
		for k in range(segs):
			try:
				f = bm.faces.new((rings[i][k], rings[i][(k + 1) % segs], rings[i + 1][(k + 1) % segs], rings[i + 1][k]))
				f.smooth = True
			except ValueError:
				pass
	if prof[0][0] > 0:
		bm.faces.new(list(reversed(rings[0])))
	mats = [m]
	if band:
		r, z0, z1, bmat = band
		mats.append(bmat)
		ring0, ring1 = [], []
		for k in range(segs + 1):
			a = 2 * math.pi * (k / segs - 0.5) - math.pi / 2       # середина этикетки смотрит на -Y (к камере)
			ring0.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z0)))
			ring1.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z1)))
		for k in range(segs):
			f = bm.faces.new((ring0[k], ring0[k + 1], ring1[k + 1], ring1[k]))
			f.material_index = 1
			f.smooth = True
			for loop, t in zip(f.loops, ((k / segs, 0), ((k + 1) / segs, 0), ((k + 1) / segs, 1), (k / segs, 1))):
				loop[uv].uv = t
	me = bpy.data.meshes.new(name)
	bm.to_mesh(me)
	bm.free()
	for mm in mats:
		me.materials.append(mm)
	o = bpy.data.objects.new(name, me)
	bpy.context.scene.collection.objects.link(o)
	o.location = loc
	return o


def cube(name, loc, size, m, bevel=0.0):
	bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
	o = bpy.context.object
	o.name = name
	o.scale = size
	o.data.materials.append(m)
	if bevel:
		md = o.modifiers.new("b", "BEVEL")
		md.width = bevel
		md.segments = 3
	return o


def light(kind, loc, energy, color=(1, 1, 1), size=1.0, target=None, spot=45):
	ld = bpy.data.lights.new("L", kind)
	ld.energy = energy
	ld.color = color
	if kind == "AREA":
		ld.size = size
	else:
		ld.shadow_soft_size = size
	if kind == "SPOT":
		ld.spot_size = math.radians(spot)
		ld.spot_blend = 0.5
	o = bpy.data.objects.new("L", ld)
	bpy.context.scene.collection.objects.link(o)
	o.location = loc
	if target:
		o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
	return o


def camera(loc, target, lens, dof_target=None, fstop=2.0):
	cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
	bpy.context.scene.collection.objects.link(cam)
	bpy.context.scene.camera = cam
	cam.location = loc
	cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
	cam.data.lens = lens
	if dof_target:
		cam.data.dof.use_dof = True
		cam.data.dof.focus_distance = (Vector(dof_target) - Vector(loc)).length
		cam.data.dof.aperture_fstop = fstop
	return cam


def img_mat(name, file, rough=0.4):
	m = bpy.data.materials.new(name)
	m.use_nodes = True
	nt = m.node_tree
	t = nt.nodes.new("ShaderNodeTexImage")
	t.image = bpy.data.images.load(os.path.join(TEX, file))
	nt.links.new(t.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
	nt.nodes["Principled BSDF"].inputs["Roughness"].default_value = rough
	return m


# =============================== 1. пиво: рекламный снимок ===============================
ONLY_STAGE = "--stage" in sys.argv
if not ONLY_STAGE:
	sc = reset()
	glass = mat("glass", (0.95, 0.97, 0.98), 0.01, trans=1.0)
	brown = mat("brown_glass", (0.42, 0.18, 0.04), 0.03, trans=1.0)
	beer = mat("beer", (0.95, 0.55, 0.08), 0.02, trans=1.0, ior=1.33)
	foam = mat("foam", (0.97, 0.95, 0.88), 0.55)
	drop = mat("drop", (1, 1, 1), 0.0, trans=1.0, ior=1.33)
	cap = mat("cap", (0.75, 0.55, 0.2), 0.25, 1.0)
	slate = mat("slate", (0.012, 0.012, 0.014), 0.22)
	label = img_mat("label", "label_beer.png", 0.45)
	s = 4.0   # масштаб: модели в 4 раза крупнее (удобнее для глубины резкости)
	BOT = [(0, 0), (0.029, 0), (0.031, 0.006), (0.031, 0.12), (0.027, 0.15), (0.014, 0.185), (0.0125, 0.215), (0.0135, 0.22), (0.0135, 0.226)]
	lathe("Bottle", [(r * s, z * s) for r, z in BOT], brown, loc=(-0.22, 0.1, 0), band=(0.0318 * s, 0.03 * s, 0.098 * s, label))
	lathe("BottleBeer", [(0, 0.01 * s)] + [(r * 0.9 * s, z * s) for r, z in BOT[1:5]] + [(0, 0.15 * s)], beer, loc=(-0.22, 0.1, 0))
	lathe("Cap", [(0, 0.218 * s), (0.0145 * s, 0.218 * s), (0.0145 * s, 0.232 * s), (0, 0.232 * s)], cap, loc=(-0.22, 0.1, 0))
	PILS = [(0, 0), (0.035, 0), (0.035, 0.008), (0.006, 0.02), (0.005, 0.07), (0.028, 0.1), (0.036, 0.15), (0.033, 0.2), (0.031, 0.215), (0.0295, 0.215), (0.0315, 0.2), (0.0345, 0.15), (0.0265, 0.1), (0.0035, 0.072)]
	lathe("Glass", [(r * s, z * s) for r, z in PILS], glass, loc=(0.12, -0.05, 0))
	lathe("Beer", [(0, 0.075 * s), (0.026 * s, 0.1 * s), (0.034 * s, 0.15 * s), (0.032 * s, 0.185 * s), (0, 0.185 * s)], beer, loc=(0.12, -0.05, 0))
	lathe("Foam", [(0, 0.185 * s), (0.032 * s, 0.185 * s), (0.033 * s, 0.2 * s), (0.031 * s, 0.222 * s), (0.02 * s, 0.232 * s), (0, 0.235 * s)], foam, loc=(0.12, -0.05, 0))
	for k in range(260):                 # капли конденсата на бокале и бутылке
		on_glass = k < 170
		cx, cy = (0.12, -0.05) if on_glass else (-0.22, 0.1)
		z = rnd.uniform(0.09, 0.18) * s if on_glass else rnd.uniform(0.01, 0.12) * s
		a = rnd.uniform(-math.pi * 0.95, -math.pi * 0.05)
		if on_glass:
			r = (0.028 + (0.036 - 0.028) * min(1, (z / s - 0.1) / 0.05)) * s if z / s < 0.15 else (0.036 - (z / s - 0.15) * 0.06) * s
		else:
			r = 0.031 * s
		bpy.ops.mesh.primitive_uv_sphere_add(radius=rnd.uniform(0.0015, 0.004), segments=10, ring_count=6, location=(cx + r * math.cos(a), cy + r * math.sin(a), z))
		o = bpy.context.object
		o.scale = (1, 1, rnd.uniform(1.0, 1.8))
		o.data.materials.append(drop)
	cube("Table", (0, 0, -0.03), (3, 3, 0.06), slate)
	wall = mat("bg", (0.004, 0.005, 0.008), 0.9)
	cube("Back", (0, 3.0, 1.5), (8, 0.05, 4), wall)
	for k in range(14):                  # огни-боке за кадром
		bpy.ops.mesh.primitive_circle_add(vertices=24, radius=rnd.uniform(0.03, 0.07), fill_type="NGON",
			location=(rnd.uniform(-1.8, 1.8), 2.9, rnd.uniform(0.3, 2.2)), rotation=(math.pi / 2, 0, 0))
		c = rnd.choice([(1, 0.6, 0.25), (0.25, 0.5, 1), (1, 0.8, 0.5)])
		bpy.context.object.data.materials.append(mat("bk%d" % k, c, emit=c, strength=12))
	light("AREA", (-1.2, -0.9, 2.2), 70, (1, 0.92, 0.8), 0.6, target=(0, 0, 0.5))
	light("AREA", (0.9, 0.9, 0.7), 260, (1, 0.6, 0.25), 0.4, target=(0.1, 0, 0.5))      # контровой тёплый
	light("AREA", (-0.9, 0.9, 0.7), 200, (0.35, 0.55, 1), 0.4, target=(-0.2, 0, 0.5))   # контровой синий
	light("AREA", (0.12, 0.6, 0.3), 60, (1, 0.7, 0.3), 0.3, target=(0.12, -0.05, 0.5))  # свет сквозь пиво
	sc.world = bpy.data.worlds.new("w")
	sc.world.color = (0.0, 0.0, 0.0)
	camera((0.0, -2.9, 0.62), (-0.05, 0, 0.5), 62, dof_target=(0.12, -0.05, 0.6), fstop=4.0)
	sc.render.filepath = os.path.join(TEX, "photo_beer.png")
	bpy.ops.render.render(write_still=True)
	print("[photo] beer", flush=True)


# =============================== 2. сцена: микрофон в дыму ===============================
sc = reset()
black = mat("black", (0.01, 0.01, 0.012), 0.5)
chrome = mat("chrome", (0.9, 0.9, 0.92), 0.12, 1.0)
grille = mat("grille", (0.5, 0.5, 0.52), 0.35, 1.0)
stage = mat("stage", (0.01, 0.01, 0.012), 0.08)
cube("Floor", (0, 0, -0.05), (12, 12, 0.1), stage)
cube("BackWall", (0, 4, 2), (12, 0.2, 5), black)
# стойка и микрофон
lathe("Base", [(0, 0), (0.16, 0), (0.17, 0.02), (0.02, 0.04), (0, 0.04)], chrome, loc=(0, 0, 0))
lathe("Pole", [(0.012, 0.04), (0.012, 1.45)], chrome, segs=24)
lathe("Clip", [(0, 1.44), (0.02, 1.44), (0.02, 1.48), (0, 1.48)], black, segs=24)
TILT = math.radians(-22)
mic = lathe("MicBody", [(0, 0), (0.014, 0), (0.017, 0.12), (0.022, 0.15), (0, 0.15)], black, loc=(0, 0, 1.47))
mic.rotation_euler = (TILT, 0, 0)
gc = (0, -math.sin(-TILT) * 0.18, 1.47 + math.cos(TILT) * 0.18)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.034, location=gc)
bpy.context.object.data.materials.append(grille)
md = bpy.context.object.modifiers.new("w", "WIREFRAME")
md.thickness = 0.0025
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.031, location=gc)
bpy.context.object.data.materials.append(black)
# усилители и барабаны (силуэты)
for x in (-1.6, 1.6):
	cube("Amp%.0f" % x, (x, 2.3, 0.6), (0.9, 0.45, 1.2), black, 0.02)
	cube("AmpGrille%.0f" % x, (x, 2.07, 0.55), (0.78, 0.01, 0.9), grille)
	cube("AmpTop%.0f" % x, (x, 2.3, 1.38), (0.9, 0.45, 0.32), black, 0.02)
for (x, y, r, h) in [(0, 3.0, 0.3, 0.55), (-0.5, 2.8, 0.2, 0.3), (0.5, 2.8, 0.2, 0.3), (0.9, 3.0, 0.25, 0.45)]:
	lathe("Drum", [(0, 0.0), (r, 0.0), (r, h), (0, h)], chrome if h < 0.35 else black, loc=(x, y, 0.4 if h < 0.35 else 0.0))
lathe("Cymbal", [(0, 0), (0.25, -0.02), (0.25, -0.015), (0, 0.005)], mat("brass", (0.8, 0.6, 0.25), 0.25, 1.0), loc=(-0.9, 2.9, 1.2))
# дым: объём в пределах сцены
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 1.5, 2))
vol = bpy.context.object
vol.scale = (8, 6, 4)
vm = bpy.data.materials.new("haze")
vm.use_nodes = True
nt = vm.node_tree
nt.nodes.remove(nt.nodes["Principled BSDF"])
vs = nt.nodes.new("ShaderNodeVolumeScatter")
vs.inputs["Density"].default_value = 0.014
nt.links.new(vs.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
vol.data.materials.append(vm)
# прожекторы сзади
for (x, y, z), tgt, c in [((-3.0, 3.5, 4.5), (0.6, -0.6, 0.0), (1.0, 0.15, 0.55)), ((3.0, 3.5, 4.5), (-0.6, -0.6, 0.0), (0.25, 0.5, 1.0)),
		((-1.2, 4.0, 5.0), (-0.3, -1.6, 0.0), (1.0, 0.45, 0.1)), ((1.2, 4.0, 5.0), (0.4, -1.6, 0.0), (0.6, 0.3, 1.0))]:
	light("SPOT", (x, y, z), 26000, c, 0.02, target=tgt, spot=7)
light("AREA", (-0.7, -0.9, 1.9), 25, (1, 0.9, 0.8), 0.25, target=(0, -0.07, 1.6))    # мягкий ключевой на микрофон
for x in (-1.6, 1.6):
	light("SPOT", (x, 1.2, 2.6), 800, (1.0, 0.5, 0.2), 0.05, target=(x, 2.3, 0.6), spot=40)   # подсветка усилителей
sc.world = bpy.data.worlds.new("w")
sc.world.color = (0, 0, 0)
sc.cycles.volume_bounces = 1
light("AREA", (0.8, 0.6, 1.9), 40, (0.5, 0.7, 1.0), 0.3, target=(0, -0.07, 1.62))   # контур микрофона
camera((0.3, -1.9, 1.5), (0.05, 0, 1.38), 70, dof_target=(0, -0.07, 1.62), fstop=2.0)
sc.render.filepath = os.path.join(TEX, "photo_stage.png")
bpy.ops.render.render(write_still=True)
print("[photo] stage", flush=True)
