# Состаривание и полумрак клуба «Neon» (дефицит электричества, лор «Карантин»).
# Подключается из build_club2.py после реквизита и света (exec, общие функции).
# 1) грязь, подтёки, сырость и высолы на стенах; 2) расклейка: листовки, рваные афиши, фанера, картон, скотч;
# 3) свет: всё в 3–4 раза тусклее, часть неона и ламп обесточена, свечи и аварийные фонари на батареях.

# --- 1. грязь на материалах ---------------------------------------------------------------
def add_grime(m, dark=0.55, streaks=True, damp=True, salt=False):
	nt = m.node_tree
	b = nt.nodes["Principled BSDF"]
	inp = b.inputs["Base Color"]
	if inp.links:
		src = inp.links[0].from_socket
	else:
		rgb = nt.nodes.new("ShaderNodeRGB")
		rgb.outputs[0].default_value = inp.default_value[:]
		src = rgb.outputs[0]
	geo = nt.nodes.new("ShaderNodeNewGeometry")
	# крупные пятна
	nz = nt.nodes.new("ShaderNodeTexNoise")
	nz.inputs["Scale"].default_value = 0.8
	nz.inputs["Detail"].default_value = 8
	nt.links.new(geo.outputs["Position"], nz.inputs["Vector"])
	f1 = nt.nodes.new("ShaderNodeMapRange")
	f1.inputs["From Min"].default_value, f1.inputs["From Max"].default_value = 0.4, 0.7
	f1.inputs["To Min"].default_value, f1.inputs["To Max"].default_value = 1.0, dark
	nt.links.new(nz.outputs["Fac"], f1.inputs[0])
	fac = f1.outputs[0]

	def mul(a, b_):
		mm = nt.nodes.new("ShaderNodeMath")
		mm.operation = "MULTIPLY"
		nt.links.new(a, mm.inputs[0])
		nt.links.new(b_, mm.inputs[1])
		return mm.outputs[0]
	if streaks:                       # вертикальные подтёки (шум растянут по высоте)
		mp = nt.nodes.new("ShaderNodeMapping")
		mp.inputs["Scale"].default_value = (7.0, 7.0, 0.35)
		nt.links.new(geo.outputs["Position"], mp.inputs[0])
		sn = nt.nodes.new("ShaderNodeTexNoise")
		sn.inputs["Scale"].default_value = 3.0
		sn.inputs["Detail"].default_value = 3
		nt.links.new(mp.outputs[0], sn.inputs["Vector"])
		f2 = nt.nodes.new("ShaderNodeMapRange")
		f2.inputs["From Min"].default_value, f2.inputs["From Max"].default_value = 0.5, 0.75
		f2.inputs["To Min"].default_value, f2.inputs["To Max"].default_value = 1.0, 0.6
		nt.links.new(sn.outputs["Fac"], f2.inputs[0])
		fac = mul(fac, f2.outputs[0])
	sep = nt.nodes.new("ShaderNodeSeparateXYZ")
	nt.links.new(geo.outputs["Position"], sep.inputs[0])
	if damp:                          # сырость у пола (1 этаж и 2 этаж)
		for base in (0.0, F2):
			f3 = nt.nodes.new("ShaderNodeMapRange")
			f3.inputs["From Min"].default_value, f3.inputs["From Max"].default_value = base + 0.0, base + 0.7
			f3.inputs["To Min"].default_value, f3.inputs["To Max"].default_value = 0.55, 1.0
			f3.clamp = True
			nt.links.new(sep.outputs[2], f3.inputs[0])
			# второй этаж: влияет только выше перекрытия
			if base > 0:
				gate = nt.nodes.new("ShaderNodeMath")
				gate.operation = "GREATER_THAN"
				gate.inputs[1].default_value = F2 - 0.05
				nt.links.new(sep.outputs[2], gate.inputs[0])
				mixf = nt.nodes.new("ShaderNodeMix")
				mixf.data_type = "FLOAT"
				nt.links.new(gate.outputs[0], mixf.inputs["Factor"])
				mixf.inputs["A"].default_value = 1.0
				nt.links.new(f3.outputs[0], mixf.inputs["B"])
				fac = mul(fac, mixf.outputs["Result"])
			else:
				fac = mul(fac, f3.outputs[0])
	comb = nt.nodes.new("ShaderNodeCombineColor")
	for i in range(3):
		nt.links.new(fac, comb.inputs[i])
	mix = nt.nodes.new("ShaderNodeMix")
	mix.data_type = "RGBA"
	mix.blend_type = "MULTIPLY"
	mix.inputs["Factor"].default_value = 1.0
	nt.links.new(src, mix.inputs[6])
	nt.links.new(comb.outputs[0], mix.inputs[7])
	out = mix.outputs[2]
	if salt:                          # белые высолы на кирпиче у пола
		sn2 = nt.nodes.new("ShaderNodeTexNoise")
		sn2.inputs["Scale"].default_value = 4.0
		sn2.inputs["Detail"].default_value = 10
		nt.links.new(geo.outputs["Position"], sn2.inputs["Vector"])
		hs = nt.nodes.new("ShaderNodeMapRange")
		hs.inputs["From Min"].default_value, hs.inputs["From Max"].default_value = 1.3, 0.2
		hs.inputs["To Min"].default_value, hs.inputs["To Max"].default_value = 0.0, 1.0
		hs.clamp = True
		nt.links.new(sep.outputs[2], hs.inputs[0])
		ns = nt.nodes.new("ShaderNodeMapRange")
		ns.inputs["From Min"].default_value, ns.inputs["From Max"].default_value = 0.55, 0.75
		ns.clamp = True
		nt.links.new(sn2.outputs["Fac"], ns.inputs[0])
		sf = mul(hs.outputs[0], ns.outputs[0])
		sm = nt.nodes.new("ShaderNodeMix")
		sm.data_type = "RGBA"
		nt.links.new(sf, sm.inputs["Factor"])
		nt.links.new(out, sm.inputs[6])
		sm.inputs[7].default_value = (0.55, 0.53, 0.5, 1)
		out = sm.outputs[2]
	nt.links.new(out, inp)
	# шероховатость: пятна матовее
	b.inputs["Roughness"].default_value = min(1.0, b.inputs["Roughness"].default_value + 0.1)


GRIME = {"brick_ns": dict(dark=0.45, salt=True), "brick_ew": dict(dark=0.45, salt=True), "tile_ns": dict(dark=0.5), "tile_ew": dict(dark=0.5),
	"wc_wall_out": dict(dark=0.5), "room_wall": dict(dark=0.6), "wall_plaster_dark": dict(dark=0.6), "ceiling": dict(dark=0.6, damp=False),
	"booth_wall": dict(dark=0.6), "tile_floor": dict(dark=0.55, streaks=False, damp=False), "kitchen_floor": dict(dark=0.55, streaks=False, damp=False),
	"parquet": dict(dark=0.6, streaks=False, damp=False), "wood_dark": dict(dark=0.7, streaks=False, damp=False)}
for name, kw in GRIME.items():
	m = bpy.data.materials.get(name)
	if m:
		add_grime(m, **kw)

# --- 2. расклейка на стенах ------------------------------------------------------------
PAPER = {k: img_mat("paper_" + k, k + ".png", 0.75, alpha=True) for k in
	["flyer_power", "flyer_cat", "flyer_cult", "flyer_trade", "flyer_gang", "flyer_concert", "flyer_missing", "flyer_liquid", "torn_layers", "tape"]}
CARD = img_mat("cardboard", "cardboard.png", 0.9)
PLY = img_mat("plywood", "plywood.png", 0.8)
import random
rr = random.Random(9)


def paste_cluster(name, c, facing, w, h, kinds, n=7, layers=True):
	"""Пятно расклейки на стене: рваные слои + листовки + скотч. c — центр на поверхности стены."""
	mb = MB()
	x, y, z = c
	nrm = {"+z": (0, 0, 1), "-z": (0, 0, -1), "+x": (1, 0, 0), "-x": (-1, 0, 0)}[facing]
	k = 0

	def off(i):
		return (x + nrm[0] * 0.002 * i, y, z + nrm[2] * 0.002 * i)
	if layers:
		u0, v0 = rr.uniform(0, 0.4), rr.uniform(0, 0.4)
		mb.quad(off(1), w * 1.15, h * 1.1, facing, PAPER["torn_layers"], uv=((u0, v0), (u0 + 0.6, v0), (u0 + 0.6, v0 + 0.6), (u0, v0 + 0.6)))
	for i in range(n):
		kind = kinds[i % len(kinds)]
		fw = rr.uniform(0.21, 0.3)
		fh = fw * 1.42
		dx, dy = rr.uniform(-w / 2 + fw / 2, w / 2 - fw / 2), rr.uniform(-h / 2 + fh / 2, h / 2 - fh / 2)
		cx = x + (dx if facing in ("+z", "-z") else 0)
		cz = z + (dx if facing in ("+x", "-x") else 0)
		p = (cx + nrm[0] * 0.002 * (i + 2), y + dy, cz + nrm[2] * 0.002 * (i + 2))
		mb.quad(p, fw, fh, facing, PAPER[kind])
		# скотч по верхним углам
		for sx in (-1, 1):
			tp = (p[0] + (sx * fw * 0.4 if facing in ("+z", "-z") else 0) + nrm[0] * 0.001, p[1] + fh * 0.47,
				p[2] + (sx * fw * 0.4 if facing in ("+x", "-x") else 0) + nrm[2] * 0.001)
			mb.quad(tp, 0.08, 0.025, facing, PAPER["tape"])
	inst(name, mb.mesh(name), (0, 0, 0))


group("F1")
paste_cluster("PasteN1", (-1.7, 1.25, -5.985), "+z", 1.8, 0.9, ["flyer_power", "flyer_concert", "flyer_cat", "flyer_trade"], 6)
paste_cluster("PasteW1", (-7.985, 1.35, 3.8), "+x", 1.6, 1.0, ["flyer_missing", "flyer_cult", "flyer_power", "flyer_gang"], 7)
paste_cluster("PasteWC", (4.885, 1.0, 4.3), "-x", 0.7, 0.5, ["flyer_cat", "flyer_trade"], 3, layers=False)
group("CUT1")
paste_cluster("PasteE1", (7.985, 1.55, 0.0), "-x", 1.4, 1.1, ["flyer_liquid", "flyer_gang", "flyer_cult", "flyer_concert"], 6)
group("F2")
paste_cluster("PasteN2", (-4.4, F2 + 1.5, -5.985), "+z", 1.3, 0.9, ["flyer_concert", "flyer_missing", "flyer_power"], 5)
paste_cluster("PasteW2", (-7.985, F2 + 1.45, 3.9), "+x", 1.2, 0.9, ["flyer_cult", "flyer_cat", "flyer_trade"], 5)
paste_cluster("PasteCorr", (4.885, F2 + 1.45, 1.1), "-x", 0.6, 0.7, ["flyer_power", "flyer_liquid"], 3, layers=False)
# фанера и картон поверх повреждённых мест
group("F1")
pm = MB()
pm.box((-7.97, 1.05, -5.2), (0.02, 1.1, 1.0), PLY)
pm.quad((-7.955, 1.05, -5.2), 1.0, 1.1, "+x", PLY)
inst("PlywoodW1", pm.mesh("plywood_w1"), (0, 0, 0))
cm = MB()
cm.quad((-0.6, 0.55, -5.985), 0.7, 0.7, "+z", CARD)
cm.quad((3.9, 2.9, 2.495), 0.8, 0.6, "-z", CARD)          # заклеенная дыра над дверью WC
inst("Cardboard1", cm.mesh("cardboard1"), (0, 0, 0))
group("CUT1")
pe = MB()
pe.quad((7.985, 1.2, -3.6), 1.2, 1.0, "-x", PLY)
inst("PlywoodE1", pe.mesh("plywood_e1"), (0, 0, 0))
group("CUT2")
p2 = MB()
p2.quad((-3.0, F2 + 1.6, 5.985), 1.3, 1.1, "-z", PLY)
inst("PlywoodS2", p2.mesh("plywood_s2"), (0, 0, 0))

# --- 3. свет: дефицит электричества ----------------------------------------------------------
DIM_LIGHT = 0.3        # все лампы
DIM_EMIT = 0.45        # неон, экраны, вывески
for o in bpy.data.objects:
	if o.type == "LIGHT":
		o.data.energy *= DIM_LIGHT
for m in bpy.data.materials:
	if m.use_nodes and "Principled BSDF" in m.node_tree.nodes:
		b = m.node_tree.nodes["Principled BSDF"]
		s = b.inputs["Emission Strength"]
		if s.default_value > 0 and not m.name.startswith(("fire", "sign_exit", "bulb_candle")):
			s.default_value *= DIM_EMIT
DEAD = mat("tube_dead", (0.12, 0.13, 0.15), 0.2)          # обесточенная трубка
OFF_OBJ = ["NeonEdgeW", "NeonEdgeN2", "NeonEdgeE", "StageEdgeW", "BarLamp1", "BarLamp3", "SlabEdgeStageLED", "JukeboxArch", "RegisterScreen"]
OFF_LIGHT = ["BarLampL1", "BarLampL3", "LampL1", "LampL3", "F2Lamp0L", "NeonB", "BoothLamp1L", "BoothLamp3L", "FloorLampL"]
for n in OFF_OBJ:
	o = bpy.data.objects.get(n)
	if o and o.type == "MESH":
		o.data.materials.clear()
		o.data.materials.append(DEAD)
for n in OFF_LIGHT:
	o = bpy.data.objects.get(n)
	if o:
		o.data.energy = 0.0
for n in ("BoothLamp1Shade", "BoothLamp3Shade", "BoothLamp1Bulb", "BoothLamp3Bulb", "F2Lamp0Bulb", "LampBulb1", "LampBulb3", "FloorLampShade"):
	o = bpy.data.objects.get(n)
	if o:
		o.data.materials.clear()
		o.data.materials.append(DEAD)
# свечи (в банках) и аварийные фонари на батареях
CANDLE = mat("bulb_candle", (1, 0.6, 0.25), 0.3, emit=(1.0, 0.55, 0.18), strength=18)
JAR = mat("candle_jar", (0.9, 0.75, 0.6), 0.1, trans=0.8)


def candle(name, pos, energy=4.0):
	x, y, z = pos
	cyl(name + "Jar", (x, y + 0.045, z), 0.035, 0.09, JAR, verts=16)
	cyl(name + "Wax", (x, y + 0.03, z), 0.03, 0.06, mat("wax", (0.9, 0.88, 0.8), 0.5), verts=16)
	sphere(name + "Flame", (x, y + 0.075, z), 0.008, CANDLE)
	light(name + "L", "POINT", (x, y + 0.09, z), energy, (1.0, 0.55, 0.2), 0.02)


def lantern(name, pos, energy=10.0):
	x, y, z = pos
	box(name + "Body", (x, y + 0.11, z), (0.12, 0.22, 0.12), mat("lantern_body", (0.7, 0.45, 0.05), 0.5))
	cyl(name + "Glow", (x, y + 0.12, z), 0.045, 0.12, mat("lantern_led", (0.9, 0.95, 1), 0.2, emit=(0.85, 0.92, 1.0), strength=12), verts=16)
	light(name + "L", "POINT", (x, y + 0.13, z), energy, (0.85, 0.9, 1.0), 0.04)


group("F1")
for i, z in enumerate([-3.5, -1.3, 0.9]):
	candle("BarCandle%d" % i, (BX + 0.3, 1.1, z), 5)
for i, (x, z) in enumerate([(-2.6, -3.2), (-2.6, -0.2), (0.4, 1.6)]):
	candle("TblCandleJ%d" % i, (x - 0.05, 1.1, z - 0.05), 5)
lantern("LanternBar", (BX - 0.3, 1.1, -4.4), 12)
lantern("LanternStage", (6.5, 0.6, -2.0), 10)
lantern("LanternWC", (6.55, 0.9, 4.3), 8)
lantern("LanternKitchen", (-4.6, 0.9, -7.6), 14)
group("F2")
for k, (x, z) in enumerate([(0.4, 0.6), (2.65, 0.6), (0.4, 2.9), (2.65, 2.9)]):
	candle("BoothCandleJ%d" % k, (x + 0.2, F2 + 0.76, z), 4)
candle("LoungeCandle0", (-5.6, F2 + 0.4, 1.4), 4)
candle("LoungeCandle1", (-6.2, F2 + 0.4, 1.8), 4)
for k, zc in enumerate([-0.15, 2.33, 4.78]):
	candle("RoomCandle%d" % k, (6.5, F2 + 0.4, zc + 0.2), 4)
lantern("LanternGames", (-2.3, F2 + 1.5, -5.6), 10)
group("F1")
