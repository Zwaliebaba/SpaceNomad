"""Build the SpaceNomad starter-frigate mining scene with Blender 4.3+.

Run: blender -b -t 8 --python create_scene.py
Environment: SCENE_OUTPUT, RENDER_SAMPLES, RENDER_SCALE, SKIP_RENDER.
The accompanying starter_frigate_source.blend is an unmodified ship library.
"""
import bpy, math, random, os, json, struct
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from math import pi, sin, cos

BASE=Path(__file__).resolve().parent
OUT=Path(os.environ.get('SCENE_OUTPUT',str(BASE)));OUT.mkdir(parents=True,exist_ok=True)
random.seed(2267)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):bpy.data.collections.remove(c)
scene=bpy.context.scene
groups={}
for name in ['MiningEquipment','OreAsteroid','AsteroidField','OreFragments','MiningEffects','Backdrop','Lighting','Cameras']:
    c=bpy.data.collections.new(name);scene.collection.children.link(c);groups[name]=c

# Append the actual starter frigate rather than rebuilding a lookalike.
library=BASE/'starter_frigate_source.blend'
source=library if library.exists() else BASE.parent/'OrionFringe'/'orion_fringe.blend'
if not source.exists():raise FileNotFoundError('Missing starter frigate source library: '+str(source))
with bpy.data.libraries.load(str(source),link=False) as (available,loaded):
    assert 'Frigate' in available.collections
    loaded.collections=['Frigate']
frigate=loaded.collections[0];scene.collection.children.link(frigate);groups['Frigate']=frigate
if not library.exists():bpy.data.libraries.write(str(library),{frigate},fake_user=True,compress=True)

view=Vector((.43,-.72,.545)).normalized();right=Vector((.858,.513,0)).normalized();up=view.cross(right).normalized()
def layout(x,y,d=0):return right*x+up*y+view*d
ship=bpy.data.objects['Frigate_ROOT'];ship.location=layout(-3.0,-.65,.6);ship.rotation_euler=(0,0,math.radians(-35))
bpy.context.view_layer.update()
def fp(x,y,z):return ship.matrix_world@Vector((x,y,z))
# Flight configuration: keep the original source library intact, retract its gear here.
for o in list(frigate.objects):
    if 'landing strut' in o.name or 'landing foot' in o.name:bpy.data.objects.remove(o,do_unlink=True)
ship['configuration']='starter frigate / mining equipment / gear retracted'
active='MiningEquipment'
def move(o,name):
    o.name=name
    for c in list(o.users_collection):c.objects.unlink(o)
    groups[active].objects.link(o);return o
def material(name,col,metal=0,rough=.5,emission=0,alpha=1):
    m=bpy.data.materials.new(name);m.diffuse_color=(*col,alpha);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*col,1)
    p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    p.inputs['Emission Color'].default_value=(*col,1);p.inputs['Emission Strength'].default_value=emission
    p.inputs['Alpha'].default_value=alpha
    if alpha<1:m.surface_render_method='DITHERED'
    return m
def assign(o,m):o.data.materials.append(m);return o
def box(name,p,size,m,bevel=.02):
    bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=move(bpy.context.object,name);o.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);assign(o,m)
    if bevel:
        b=o.modifiers.new('Machined edges','BEVEL');b.width=bevel;b.segments=1;o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    return o
def beam(name,a,b,r,m,verts=12):
    a,b=Vector(a),Vector(b);bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=(b-a).length,location=(a+b)/2)
    o=assign(move(bpy.context.object,name),m);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def parent_keep(o,root):
    bpy.context.view_layer.update();w=o.matrix_world.copy();o.parent=root;o.matrix_world=w
def root(name,group,p):
    r=bpy.data.objects.new(name,None);groups[group].objects.link(r);r.location=p;bpy.context.view_layer.update();return r
def point(name,p,color,power,size=.15):
    d=bpy.data.lights.new(name,'POINT');d.energy=power;d.color=color;d.shadow_soft_size=size
    o=bpy.data.objects.new(name,d);groups['Lighting'].objects.link(o);o.location=p;return o
armor=bpy.data.materials['Armor | blue grey ceramic'];dark=bpy.data.materials['Structure | graphite']
orange=bpy.data.materials['Trim | burnt orange'];metal=bpy.data.materials['Armor | pale titanium']
ore_mats=[material('Ore | hematite',(.19,.08,.033),.8,.4),material('Ore | copper',(.48,.20,.055),.78,.34),material('Ore | pale pyrite',(.62,.43,.15),.85,.32)]
rock_mats=[material('Asteroid | basalt %02d'%i,(.065+i*.012,.080+i*.013,.10+i*.016),.17,.88) for i in range(6)]
hot=material('Mining | hot contact',(1,.28,.025),0,.3,5)
laser=material('Mining | white amber core',(1,.66,.18),0,.3,7)
halo=material('Mining | amber halo',(1,.20,.012),0,.4,1.2,.10)
spark=material('Mining | incandescent sparks',(1,.52,.10),0,.3,7)
engine=material('Drive | stationkeeping blue',(.02,.35,1),0,.4,2)
exhaust=material('Drive | short ion plume',(.01,.15,1),0,.4,1,.08)
tractor=material('Mining | ore retrieval cyan',(.02,.65,1),0,.4,2,.18)

# Belly bay covers and twin articulated mining mounts are removable attachments.
for x in [-.25,.25]:
    o=box('Mining rig | closed landing bay',fp(x,0,-.21),(.33,.87,.045),dark,.012);o.rotation_euler=ship.rotation_euler;parent_keep(o,ship)
for side in [-1,1]:
    o=box('Mining rig | attachment hardpoint',fp(side*.56,.48,.10),(.19,.36,.25),orange,.025)
    o.rotation_euler=ship.rotation_euler;parent_keep(o,ship)
    o=beam('Mining rig | articulated arm',fp(side*.56,.56,.12),fp(side*.76,1.02,.12),.055,metal,8);parent_keep(o,ship)

# Low-poly mineable asteroid; its exposed metals are reflective, not self-illuminated.
active='OreAsteroid';ore_center=layout(1.55,.60,-.7)
ore_root=root('OreAsteroid_ROOT','OreAsteroid',ore_center)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3,radius=1.8,location=ore_center);ore=move(bpy.context.object,'Ore asteroid | fractured basalt')
for v in ore.data.vertices:
    v.co*=random.uniform(.87,1.14);v.co.x*=1.12;v.co.y*=.90
for m in rock_mats+ore_mats:ore.data.materials.append(m)
exposed=(-right*.72+view*.70+up*.15).normalized()
ore.data.update()
for face in ore.data.polygons:
    if face.normal.dot(exposed)>.25 and random.random()<.55:face.material_index=random.randrange(6,9)
    else:face.material_index=random.randrange(6)
parent_keep(ore,ore_root);bpy.context.view_layer.update()
world_vertices=[ore.matrix_world@v.co for v in ore.data.vertices]
bvh=BVHTree.FromPolygons(world_vertices,[list(p.vertices) for p in ore.data.polygons])

# Mineral outcrops follow exposed asteroid facets, with their roots embedded in rock.
for face in random.sample(list(ore.data.polygons),100):
    if face.material_index<6 or face.normal.dot(exposed)<.30:continue
    c=ore.matrix_world@face.center;n=face.normal.normalized()
    bpy.ops.mesh.primitive_cone_add(vertices=5,radius1=random.uniform(.07,.13),radius2=.02,depth=random.uniform(.12,.25),location=c+n*.045)
    crystal=assign(move(bpy.context.object,'Ore asteroid | metallic outcrop'),ore_mats[face.material_index-6]);crystal.rotation_euler=n.to_track_quat('Z','Y').to_euler();parent_keep(crystal,ore_root)

# Ray-cast both drills onto the actual rock surface: no beams through the asteroid.
hits=[];emitters=[]
for side in [-1,1]:
    origin=fp(side*.76,1.02,.12)
    aim=ore_center+right*(side*.26)+up*(.12 if side<0 else -.10)
    direction=(aim-origin).normalized();hit,normal,index,distance=bvh.ray_cast(origin,direction,20)
    assert hit is not None,'Mining beam missed asteroid'
    active='MiningEquipment'
    mouth=origin+direction*.28
    o=beam('Mining rig | drill barrel',origin,mouth,.085,dark,10);parent_keep(o,ship)
    o=beam('Mining rig | copper focusing collar',mouth-direction*.09,mouth-direction*.02,.10,orange,10);parent_keep(o,ship)
    o=beam('Mining rig | emitter lens',mouth-direction*.012,mouth,.064,laser,12);parent_keep(o,ship)
    socket=bpy.data.objects.new('MiningEmitter_'+('L' if side<0 else 'R'),None);groups[active].objects.link(socket);socket.location=mouth;parent_keep(socket,ship)
    active='MiningEffects'
    beam('Mining beam | bright core',mouth,hit,.012,laser)
    beam('Mining beam | halo',mouth,hit,.035,halo)
    # Burn scar and hot rim are presentation effects; keep the mineable rock reusable.
    disc=beam('Mining impact | dark excavation scar',hit-normal*.006,hit+normal*.012,.19,dark,14)
    bpy.ops.mesh.primitive_torus_add(major_segments=24,minor_segments=4,major_radius=.12,minor_radius=.012,location=hit+normal*.023)
    ring=assign(move(bpy.context.object,'Mining impact | hot rim'),hot);ring.rotation_euler=normal.to_track_quat('Z','Y').to_euler()
    point('Mining impact | amber bounce',hit+normal*.16,(1,.25,.035),12,.16)
    for i in range(28):
        tangent=Vector((random.uniform(-1,1),random.uniform(-1,1),random.uniform(-1,1)))
        vel=(normal*.7+tangent*.65).normalized();start=hit+normal*.04+vel*random.uniform(.03,.35)
        beam('Mining impact | spark',start,start+vel*random.uniform(.025,.12),random.uniform(.003,.006),spark,5)
    target=bpy.data.objects.new('MiningTarget_'+('L' if side<0 else 'R'),None);groups['OreAsteroid'].objects.link(target);target.location=hit;parent_keep(target,ore_root)
    hits.append(hit);emitters.append(mouth)

# Flying ore chips and a subtle cyan retrieval tether make extraction readable.
active='OreFragments'
fragments=[]
for i in range(14):
    t=random.uniform(.05,.62);p=hits[i%2].lerp(fp(0,.65,-.05),t)+layout(random.uniform(-.25,.25),random.uniform(-.35,.35),random.uniform(-.2,.2))
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=random.uniform(.035,.09),location=p)
    o=assign(move(bpy.context.object,'Ore fragment | %02d'%i),ore_mats[i%3]);o.scale=(1,random.uniform(.6,1.3),random.uniform(.7,1.4));fragments.append(o)
active='MiningEffects'
retrieval=fp(0,.75,-.15);beam('Ore retrieval | cyan tether',retrieval,fragments[7].location,.008,tractor,8)
active='MiningEquipment'
o=box('Mining rig | ore collection port',fp(0,.65,-.20),(.25,.27,.06),metal,.015);o.rotation_euler=ship.rotation_euler;parent_keep(o,ship)

# Short blue drive glow keeps the frigate visibly under stationkeeping thrust.
active='MiningEffects'
for side in [-1,1]:
    a,b=fp(side*.35,-1.37,-.015),fp(side*.35,-2.00,-.015)
    plume=beam('Drive | stationkeeping plume',a,b,.11,exhaust,16)
    for v in plume.data.vertices:
        if v.co.z>0:v.co.x*=.04;v.co.y*=.04
    point('Drive | blue bounce',a,(.015,.3,1),1.8,.12)

active='AsteroidField'
field=[(-5.4,2.6,-3,.72),(-.3,3.6,-6,.55),(4.8,2.6,-4,.62),(5.7,-3.25,1.5,1.5),(-5.8,-3.0,-1,.78),(-.4,-3.1,-3,.48),(4.8,-.7,-6,.32),(-2.4,2.3,-7,.24),(2.6,-3.4,-5,.22),(-5.7,.2,-5,.20)]
for i,(x,y,d,r) in enumerate(field):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2 if r>.5 else 1,radius=r,location=layout(x,y,d));o=move(bpy.context.object,'Field asteroid | %02d'%i)
    for v in o.data.vertices:v.co*=random.uniform(.8,1.18)
    o.scale=(random.uniform(.8,1.2),random.uniform(.8,1.2),random.uniform(.8,1.2))
    o.rotation_euler=[random.random()*6 for _ in range(3)]
    for m in rock_mats:o.data.materials.append(m)
    for f in o.data.polygons:f.material_index=random.randrange(6)

# Starfield and a quiet blue nebula support the action without a HUD or station.
active='Backdrop'
neb=material('Backdrop | blue dust',(.004,.012,.026),0,1,1)
n=neb.node_tree.nodes;l=neb.node_tree.links;p=n.get('Principled BSDF');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=3;noise.inputs['Detail'].default_value=4
coord=n.new('ShaderNodeTexCoord');ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.001,.003,.008,1);ramp.color_ramp.elements[1].color=(.012,.031,.055,1)
l.new(coord.outputs['Generated'],noise.inputs['Vector']);l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Emission Color'])
o=box('Backdrop | dust cloud',layout(0,0,-45),(40,30,.02),neb,0);o.rotation_euler=view.to_track_quat('Z','Y').to_euler()
stars=material('Backdrop | stars',(.56,.72,1),0,1,2)
vs=[];faces=[]
for i in range(450):
    p=layout(random.uniform(-11,11),random.uniform(-7,7),-35);r=random.choices([.003,.007,.012],[7,4,1])[0];j=len(vs)
    vs.extend([p-right*r-up*r,p+right*r-up*r,p+right*r+up*r,p-right*r+up*r]);faces.append((j,j+1,j+2,j+3))
me=bpy.data.meshes.new('Star quads');me.from_pydata(vs,[],faces);me.update();o=bpy.data.objects.new('Backdrop | starfield',me);groups[active].objects.link(o);assign(o,stars)

active='Cameras'
bpy.ops.object.camera_add(location=layout(0,0,35));camera=move(bpy.context.object,'Camera | mining overview');camera.rotation_euler=(-view).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=12.8;scene.camera=camera
active='Lighting'
world=bpy.data.worlds.new('Mining field | deep space');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.04,.065,.11,1);world.node_tree.nodes['Background'].inputs[1].default_value=.28;scene.world=world
d=bpy.data.lights.new('Sun | cool starlight','SUN');d.energy=2.1;d.angle=.10;d.color=(.65,.76,1)
o=bpy.data.objects.new(d.name,d);groups[active].objects.link(o);o.rotation_euler=(.45,-.6,-.5)
def area(name,p,target,power,color,size):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.color=color;d.shape='DISK';d.size=size
    o=bpy.data.objects.new(name,d);groups['Lighting'].objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
area('Key | warm industrial rim',layout(-3,4,7),ore_center,190,(1,.64,.36),6)
area('Fill | blue hull readability',layout(-3,1,6),ship.location,150,(.37,.57,1),5)

# Validate the actual flight configuration and drill intersections before saving.
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();min_distance=100
for o in groups['Frigate'].objects:
    if o.type!='MESH':continue
    e=o.evaluated_get(deps);m=e.to_mesh()
    for v in m.vertices:
        p=o.matrix_world@v.co;nearest,normal,index,dist=bvh.find_nearest(p);min_distance=min(min_distance,dist)
    e.to_mesh_clear()
assert min_distance>.5,('Hull too close to asteroid',min_distance)
for a,b in zip(emitters,hits):
    hit,normal,index,dist=bvh.ray_cast(a,(b-a).normalized(),20)
    assert hit is not None and (hit-b).length<.005,'Beam does not stop at rock surface'
assert not any('Station' in o.name or 'Cruiser' in o.name for o in scene.objects)
assert not any('landing foot' in o.name or 'landing strut' in o.name for o in scene.objects)
scene['description']='Starter frigate extracting metallic ore in an asteroid belt; no station or HUD.'
scene['seed']=2267
scene.render.engine='CYCLES';scene.cycles.samples=int(os.environ.get('RENDER_SAMPLES','64'));scene.cycles.use_denoising=bool(getattr(bpy.app.build_options,'openimagedenoise',False))
scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=int(os.environ.get('RENDER_SCALE','100'))
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(OUT/'asteroid_mining_preview.png');scene.view_settings.view_transform='AgX'
scene.use_nodes=True;n=scene.node_tree.nodes;n.clear();l=scene.node_tree.links
rl=n.new('CompositorNodeRLayers');gl=n.new('CompositorNodeGlare');gl.glare_type='FOG_GLOW';gl.quality='HIGH';gl.threshold=1.4;gl.size=7;output=n.new('CompositorNodeComposite');l.new(rl.outputs['Image'],gl.inputs[0]);l.new(gl.outputs[0],output.inputs[0])
bpy.ops.object.select_all(action='DESELECT')
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':a.spaces.active.region_3d.view_perspective='CAMERA';a.spaces.active.overlay.show_overlays=False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'asteroid_mining.blend'),compress=True)
exports={'mining_frigate':['Frigate','MiningEquipment'],'ore_asteroid':['OreAsteroid'],'asteroid_field':['AsteroidField','OreFragments'],'mining_effects':['MiningEffects']}
stats={}
for name,collections in exports.items():
    bpy.ops.object.select_all(action='DESELECT')
    for collection in collections:
        for o in groups[collection].objects:o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(OUT/(name+'.glb')),export_format='GLB',use_selection=True,export_apply=True,export_yup=True)
    raw=(OUT/(name+'.glb')).read_bytes();length=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+length])
    stats[name]={'triangles':sum(g['accessors'][p['indices']]['count']//3 for m in g.get('meshes',[]) for p in m['primitives'])}
bpy.ops.object.select_all(action='DESELECT')
manifest={'seed':2267,'units':'metres','blender_up':'+Z','gltf_up':'+Y','ship_forward':'+Y','source':'starter_frigate_source.blend / Frigate collection','assets':stats,'mining':{'beam_count':len(hits),'surface_hits':[list(v) for v in hits],'emitters':[list(v) for v in emitters],'minimum_hull_surface_distance':min_distance,'ore_fragments':len(fragments)},'presentation':'Static mining vignette. Beam, spark and drive meshes are separate effects; game extraction logic and engine particle effects are not implemented.'}
(OUT/'scene_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('MINING_VALIDATION_OK',json.dumps(manifest['mining']),flush=True)
if not os.environ.get('SKIP_RENDER'):bpy.ops.render.render(write_still=True)
print('MINING_SCENE_COMPLETE',str(OUT),flush=True)
