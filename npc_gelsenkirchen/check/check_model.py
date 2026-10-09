import bpy, sys, json, math, mathutils
glb, out = sys.argv[1], sys.argv[2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
allm=[o for o in sc.objects if o.type=='MESH']
for o in allm:
    if o.name.startswith('Icosphere'): o.hide_render=True
meshes=[o for o in allm if not o.name.startswith('Icosphere')]; arms=[o for o in sc.objects if o.type=='ARMATURE']
dg=bpy.context.evaluated_depsgraph_get()
rep={"meshes":[],"armatures":[],"actions":[],"materials":[]}
tri=0; mn=mathutils.Vector((1e9,)*3); mx=-mn
for o in meshes:
    e=o.evaluated_get(dg); m=e.to_mesh(); m.calc_loop_triangles(); t=len(m.loop_triangles); tri+=t
    for v in m.vertices:
        w=o.matrix_world@v.co; mn=mathutils.Vector(map(min,mn,w)); mx=mathutils.Vector(map(max,mx,w))
    rep["meshes"].append({"name":o.name,"tris":t,"verts":len(m.vertices),"mats":[s.material.name for s in o.material_slots if s.material],"shape_keys":len(o.data.shape_keys.key_blocks) if o.data.shape_keys else 0,"vgroups":len(o.vertex_groups)})
    e.to_mesh_clear()
for a in arms: rep["armatures"].append({"name":a.name,"bones":len(a.data.bones),"sample":[b.name for b in a.data.bones][:12]})
for ac in bpy.data.actions: rep["actions"].append({"name":ac.name,"frames":[round(x) for x in ac.frame_range]})
for mt in bpy.data.materials:
    imgs=[n.image.name+" %dx%d"%tuple(n.image.size) for n in (mt.node_tree.nodes if mt.use_nodes else []) if n.type=='TEX_IMAGE' and n.image]
    rep["materials"].append({"name":mt.name,"textures":imgs})
rep['icosphere_info']=[{'name':o.name,'parent':o.parent.name if o.parent else None,'hide_render_in_file':o.hide_get(),'dims':list(o.dimensions)} for o in allm if o.name.startswith('Icosphere')]
rep["total_tris"]=tri; rep["bbox_min"]=list(mn); rep["bbox_max"]=list(mx); rep["height_m"]=mx.z-mn.z
json.dump(rep,open(out+"/report.json","w"),indent=1,ensure_ascii=False)
# render setup
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=24; sc.cycles.use_denoising=True
for ang,en in [((50,0,35),4),((60,0,-140),2),((80,0,180),1.5)]:
    L=bpy.data.objects.new("L",bpy.data.lights.new("L","SUN")); L.data.energy=en; L.rotation_euler=[math.radians(x) for x in ang]; sc.collection.objects.link(L)
sc.render.resolution_x=720; sc.render.resolution_y=1080; sc.render.film_transparent=False
sc.world=bpy.data.worlds.new("w"); sc.world.color=(0.25,0.25,0.28)
c=(mn+mx)/2; h=mx.z-mn.z
cam=bpy.data.objects.new("cam",bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera=cam
cam.data.lens=70
def shot(name,ang,zf=0.5,dist=None,tgt=None,lens=70):
    cam.data.lens=lens; d=dist or h*2.6; t=tgt or mathutils.Vector((c.x,c.y,mn.z+h*zf))
    cam.location=t+mathutils.Vector((math.sin(ang)*d,-math.cos(ang)*d,0))
    cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=f"{out}/{name}.png"; bpy.ops.render.render(write_still=True)
# frame of first idle-like action
if arms and arms[0].animation_data and bpy.data.actions:
    idle=bpy.data.actions.get('idle',bpy.data.actions[0])
    arms[0].animation_data.action=idle; sc.frame_set(int(idle.frame_range[0])+10)
dg=bpy.context.evaluated_depsgraph_get()
mn=mathutils.Vector((1e9,)*3); mx=-mn
for o in meshes:
    e=o.evaluated_get(dg); m=e.to_mesh()
    for v in m.vertices:
        w=e.matrix_world@v.co; mn=mathutils.Vector(map(min,mn,w)); mx=mathutils.Vector(map(max,mx,w))
    e.to_mesh_clear()
c=(mn+mx)/2; h=mx.z-mn.z; print('POSED',list(mn),list(mx),h)
rep['posed_height_idle']=h; json.dump(rep,open(out+'/report.json','w'),indent=1,ensure_ascii=False)
for n,a in [("front",0),("side",math.pi/2),("back",math.pi),("three_quarter",math.pi/4)]: shot(n,a)
shot("face",0.3,zf=0.92,dist=h*0.32)
clay=bpy.data.materials.new("clay")
for o in meshes:
    o.data.materials.clear() if False else None
    for i in range(len(o.material_slots)): o.material_slots[i].link='OBJECT'; o.material_slots[i].material=clay
shot("clay_front",0.0); shot("clay_side",math.pi/2)
for o in meshes:
    for i in range(len(o.material_slots)): o.material_slots[i].link='DATA'
bpy.ops.wm.save_as_mainfile(filepath=out+"/model_check.blend")
