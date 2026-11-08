"""Build the SpaceNomad starter-frigate combat scene with Blender 4.3+.

Run: blender -b -t 8 --python create_scene.py
Environment: SCENE_OUTPUT, RENDER_SAMPLES, RENDER_SCALE, SKIP_RENDER.
The accompanying starter_frigate_source.blend is an unmodified ship library.
"""
import bpy, bmesh, math, random, os, json, struct
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from math import pi, sin, cos

BASE=Path(__file__).resolve().parent
OUT=Path(os.environ.get('SCENE_OUTPUT',str(BASE)));OUT.mkdir(parents=True,exist_ok=True)
random.seed(2268)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):bpy.data.collections.remove(c)
scene=bpy.context.scene
groups={}
for name in ['HumanEquipment','AlienFrigate','BattleEffects','AsteroidField','Backdrop','Lighting','Cameras']:
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
ship['configuration']='starter frigate / combat / gear retracted'
active='HumanEquipment'
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

armor=bpy.data.materials['Armor | blue grey ceramic'];dark=bpy.data.materials['Structure | graphite'];metal=bpy.data.materials['Armor | pale titanium']
human_shot=material('Human | blue-white pulse',(.20,.65,1),0,.3,7)
human_halo=material('Human | pulse bloom',(.02,.33,1),0,.4,2,.10)
human_shield=material('Human | shield cyan',(.015,.48,1),0,.4,1.6,.12)
human_ripple=material('Human | shield edge',(.06,.65,1),0,.4,2,.42)
jade=material('Veyr | deep jade carapace',(.025,.14,.115),.55,.36)
ivory=material('Veyr | ivory armor',(.64,.60,.45),.35,.4)
teal=material('Veyr | jade edge',(.045,.31,.24),.65,.32)
bronze=material('Veyr | bronze seams',(.36,.22,.09),.72,.4)
alien_dark=material('Veyr | dark internal structure',(.012,.028,.035),.75,.4)
reactor=material('Veyr | violet reactor',(.48,.035,.9),.2,.3,2)
plasma=material('Veyr | magenta plasma',(.8,.055,1),0,.3,6)
plasma_halo=material('Veyr | plasma halo',(.6,.015,1),0,.4,2,.12)
alien_shield=material('Veyr | shield jade',(.015,.65,.39),0,.4,1.5,.10)
alien_ripple=material('Veyr | shield edge',(.08,.9,.55),0,.4,2,.40)
hot=material('Battle | white impact',(.7,.85,1),0,.3,8)
blue_plume=material('Human | drive plume',(.01,.15,1),0,.5,1.3,.10)
violet_plume=material('Veyr | drive plume',(.4,.015,1),0,.5,1.3,.10)
rock_mats=[material('Rock | battle field %02d'%i,(.065+i*.012,.080+i*.013,.10+i*.016),.17,.88) for i in range(6)]

ship.rotation_euler.y=math.radians(6);bpy.context.view_layer.update()
for x in [-.25,.25]:
    o=box('Human | closed landing bay',fp(x,0,-.21),(.33,.87,.045),dark,.012);o.rotation_euler=ship.rotation_euler;parent_keep(o,ship)

# Alien peer frigate: a faceted central spine and two swept crescent blades.
active='AlienFrigate';alien=root('VeyrFrigate_ROOT','AlienFrigate',layout(3,.70,-.35))
alien.rotation_euler=(0,math.radians(-8),math.radians(145));alien['faction']='Veyr (working concept)';alien['class']='frigate';alien['forward_axis']='+Y'
bpy.context.view_layer.update()
def ep(x,y,z):return alien.matrix_world@Vector((x,y,z))
def prism(name,outline,low,high,m,bevel=.025):
    vs=[(x,y,low) for x,y in outline]+[(x,y,high) for x,y in outline];count=len(outline)
    fs=[tuple(reversed(range(count))),tuple(range(count,count*2))]+[(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update()
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
    o=bpy.data.objects.new(name,me);groups['AlienFrigate'].objects.link(o);assign(o,m);o.parent=alien
    if bevel:
        b=o.modifiers.new('Carapace edges','BEVEL');b.width=bevel;b.segments=1;o.modifiers.new('Facet normals','WEIGHTED_NORMAL')
    return o
prism('Veyr | central keel',[(0,1.18),(.38,.50),(.48,-.42),(.22,-1.16),(0,-1.4),(-.22,-1.16),(-.48,-.42),(-.38,.50)],-.18,.17,jade)
prism('Veyr | dorsal shell',[(0,.94),(.27,.40),(.32,-.40),(0,-1.10),(-.32,-.40),(-.27,.40)],.17,.32,ivory)
blade=[(.32,-1.05),(.90,-.85),(1.38,-.15),(1.42,.60),(1.05,1.55),(.73,1.18),(.92,.37),(.78,-.20),(.35,-.47)]
for side in [-1,1]:
    shape=[(x*side,y) for x,y in blade];prism('Veyr | swept blade '+str(side),shape,-.11,.17,jade)
    cx=sum(x for x,y in shape)/len(shape);cy=sum(y for x,y in shape)/len(shape)
    top=[(cx+(x-cx)*.84,cy+(y-cy)*.88) for x,y in shape];prism('Veyr | ivory blade plate '+str(side),top,.17,.28,ivory,.018)
    for a,b in [((.66,-.70,.30),(1.12,-.10,.30)),((1.12,-.10,.30),(1.19,.56,.30)),((1.19,.56,.30),(1.04,1.27,.23))]:
        o=beam('Veyr | inlaid jade conduit',ep(a[0]*side,a[1],a[2]),ep(b[0]*side,b[1],b[2]),.025,teal,6);parent_keep(o,alien)
    for y,x in [(-.50,.70),(.10,1.10),(.75,1.09)]:
        o=beam('Veyr | bronze carapace seam',ep(side*(x-.10),y,.29),ep(side*(x+.09),y+.06,.29),.012,bronze,6);parent_keep(o,alien)
    o=beam('Veyr | plasma emitter housing',ep(side*1.03,1.24,.12),ep(side*1.05,1.54,.12),.07,alien_dark,10);parent_keep(o,alien)
    o=beam('Veyr | plasma emitter lens',ep(side*1.05,1.52,.12),ep(side*1.05,1.56,.12),.052,plasma,10);parent_keep(o,alien)
for x in [-.18,.18]:
    o=beam('Veyr | aft drive housing',ep(x,-1.05,0),ep(x,-1.43,0),.14,alien_dark,10);parent_keep(o,alien)
    o=beam('Veyr | violet drive core',ep(x,-1.43,0),ep(x,-1.45,0),.095,reactor,12);parent_keep(o,alien)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=ep(0,-.10,.38));o=assign(move(bpy.context.object,'Veyr | faceted command crystal'),reactor)
o.scale=(.21,.42,.16);o.rotation_euler=alien.rotation_euler;parent_keep(o,alien)
for side in [-1,1]:
    o=beam('Veyr | dorsal spine fin',ep(side*.17,-.52,.30),ep(side*.24,-.75,.70),.04,jade,5);parent_keep(o,alien)

# Analytic ellipsoid shields provide repeatable projectile contact points.
def shield_hit(origin,target,root,radii):
    origin,target=Vector(origin),Vector(target);direction=(target-origin).normalized();inv=root.matrix_world.inverted()
    local=inv@origin;axis=inv.to_3x3()@direction
    a=sum((axis[i]/radii[i])**2 for i in range(3));b=2*sum(local[i]*axis[i]/radii[i]**2 for i in range(3));c=sum((local[i]/radii[i])**2 for i in range(3))-1
    discriminant=b*b-4*a*c;assert discriminant>0,'Shot missed shield volume'
    t=(-b-math.sqrt(discriminant))/(2*a);assert t>0
    hit=origin+direction*t;v=inv@hit
    normal=(root.matrix_world.to_3x3()@Vector([v[i]/radii[i]**2 for i in range(3)])).normalized()
    assert abs(sum((v[i]/radii[i])**2 for i in range(3))-1)<.0001
    return hit,normal
alien_radii=(1.8,1.92,.90);human_radii=(1.0,1.65,.88)
active='HumanEquipment'
# Keep the starter's existing turret, aiming only its barrel at the opponent.
old=bpy.data.objects['Frigate | short defense barrel'];bpy.data.objects.remove(old,do_unlink=True)
a=fp(0,-.10,.50);direction=(alien.location+view*.4-a).normalized();human_muzzle=a+direction*.32
o=beam('Human | aimed original defense barrel',a,human_muzzle,.025,dark,8);parent_keep(o,ship)
socket=bpy.data.objects.new('HumanWeaponEmitter',None);groups[active].objects.link(socket);socket.location=human_muzzle;parent_keep(socket,ship)
alien_hit,alien_normal=shield_hit(human_muzzle,alien.location+view*.40,alien,alien_radii)
enemy_emitters=[ep(side*1.05,1.56,.12) for side in [-1,1]]
human_hits=[]
for i,start in enumerate(enemy_emitters):
    p,n=shield_hit(start,ship.location+view*.47+right*((i-.5)*.08),ship,human_radii);human_hits.append((p,n))
    active='AlienFrigate';socket=bpy.data.objects.new('VeyrWeaponEmitter_'+str(i+1),None);groups[active].objects.link(socket);socket.location=start;parent_keep(socket,alien)

active='BattleEffects'
def pulse(name,start,end,fraction,length,r,m,glow):
    start,end=Vector(start),Vector(end);direction=(end-start).normalized();mid=start.lerp(end,fraction)
    beam(name+' | core',mid-direction*length*.5,mid+direction*length*.5,r,m,8)
    beam(name+' | soft edge',mid-direction*length*.5,mid+direction*length*.5,r*2.3,glow,8)
for f in [.14,.42,.70,.91]:pulse('Human | pulse bolt',human_muzzle,alien_hit,f,.18,.014,human_shot,human_halo)
for i,(start,(target,n)) in enumerate(zip(enemy_emitters,human_hits)):
    for f in [.18,.50,.80]:pulse('Veyr | plasma bolt',start,target,f,.14,.024,plasma,plasma_halo)

def impact(name,p,normal,r,shield_m,ripple_m,flash_m):
    # A curved, localized patch avoids covering the ships in a full-screen bubble.
    p,normal=Vector(p),Vector(normal);tx=normal.cross(view)
    if tx.length<.01:tx=normal.cross(right)
    tx.normalize();ty=normal.cross(tx).normalized();vs=[p+normal*.008];fs=[]
    for j in range(40):
        a=2*pi*j/40;vs.append(p+tx*cos(a)*r+ty*sin(a)*r-normal*(r*r/(2*1.8)))
    for j in range(40):fs.append((0,j+1,(j+1)%40+1))
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name+' | curved shield patch',me);groups[active].objects.link(o);assign(o,shield_m)
    for radius in [r*.45,r*.88]:
        bpy.ops.mesh.primitive_torus_add(major_segments=40,minor_segments=4,major_radius=radius,minor_radius=.008,location=p-normal*(radius*radius/(2*1.8)))
        o=assign(move(bpy.context.object,name+' | shield ripple'),ripple_m);o.rotation_euler=normal.to_track_quat('Z','Y').to_euler()
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.05,location=p+normal*.02);assign(move(bpy.context.object,name+' | energy flash'),flash_m)
    for j in range(14):
        tangent=(tx*random.uniform(-1,1)+ty*random.uniform(-1,1)+normal*.6).normalized()
        a=p+normal*.025+tangent*random.uniform(.03,.13)
        beam(name+' | energy arc',a,a+tangent*random.uniform(.035,.10),.004,flash_m,5)
    return p
impact('Veyr shield impact',alien_hit,alien_normal,.38,alien_shield,alien_ripple,hot)
impact('Human shield impact',human_hits[0][0],human_hits[0][1],.29,human_shield,human_ripple,plasma)
point('Veyr shield | blue pulse bounce',alien_hit+alien_normal*.15,(.08,.55,1),8,.16)
point('Human shield | violet plasma bounce',human_hits[0][0]+human_hits[0][1]*.13,(.6,.04,1),6,.16)
for name,p,m in [('Human muzzle flash',human_muzzle,human_shot)]+[('Veyr muzzle flash',p,plasma) for p in enemy_emitters]:
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.035,location=p);assign(move(bpy.context.object,name),m)

# Ship-local drive plumes remain separate from the exportable hulls.
for owner,fn,offsets,material_,radius,length in [(ship,fp,[-.35,.35],blue_plume,.11,.85),(alien,ep,[-.18,.18],violet_plume,.095,.8)]:
    y=-1.37 if owner==ship else -1.46
    for x in offsets:
        plume=beam(owner.name+' | drive plume',fn(x,y,-.015),fn(x,y-length,-.015),radius,material_,16)
        for v in plume.data.vertices:
            if v.co.z>0:v.co.x*=.04;v.co.y*=.04

active='AsteroidField'
field=[(-5.3,3,-5,.75),(5.5,-3.5,2,1.2),(-5.4,-3.3,2,.9),(.3,3.6,-8,.55),(5.1,2.8,-7,.5),(-.8,-3.7,-5,.28),(-5,1.0,-5,.20)]
for i,(x,y,d,r) in enumerate(field):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2 if r>.5 else 1,radius=r,location=layout(x,y,d));o=move(bpy.context.object,'Battlefield asteroid | %02d'%i)
    for v in o.data.vertices:v.co*=random.uniform(.82,1.15)
    o.rotation_euler=[random.random()*6 for _ in range(3)]
    for m in rock_mats:o.data.materials.append(m)
    for f in o.data.polygons:f.material_index=random.randrange(6)

active='Backdrop'
neb=material('Backdrop | blue violet dust',(.003,.009,.021),0,1,1)
n=neb.node_tree.nodes;l=neb.node_tree.links;p=n.get('Principled BSDF');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=3;noise.inputs['Detail'].default_value=4
coord=n.new('ShaderNodeTexCoord');ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.001,.003,.008,1);ramp.color_ramp.elements[1].color=(.022,.025,.055,1)
l.new(coord.outputs['Generated'],noise.inputs['Vector']);l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Emission Color'])
o=box('Backdrop | dust cloud',layout(0,0,-45),(40,30,.02),neb,0);o.rotation_euler=view.to_track_quat('Z','Y').to_euler()
stars=material('Backdrop | stars',(.56,.72,1),0,1,2);vs=[];fs=[]
for i in range(400):
    p=layout(random.uniform(-11,11),random.uniform(-7,7),-35);r=random.choices([.003,.007,.012],[7,4,1])[0];j=len(vs)
    vs.extend([p-right*r-up*r,p+right*r-up*r,p+right*r+up*r,p-right*r+up*r]);fs.append((j,j+1,j+2,j+3))
me=bpy.data.meshes.new('Star quads');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new('Backdrop | starfield',me);groups[active].objects.link(o);assign(o,stars)

active='Cameras'
bpy.ops.object.camera_add(location=layout(0,0,35));camera=move(bpy.context.object,'Camera | frigate duel');camera.rotation_euler=(-view).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=12.5;scene.camera=camera
active='Lighting'
world=bpy.data.worlds.new('Frigate duel | deep space');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.04,.065,.11,1);world.node_tree.nodes['Background'].inputs[1].default_value=.28;scene.world=world
d=bpy.data.lights.new('Sun | cool starlight','SUN');d.energy=2.1;d.angle=.10;d.color=(.65,.76,1)
o=bpy.data.objects.new(d.name,d);groups[active].objects.link(o);o.rotation_euler=(.45,-.6,-.5)
def area(name,p,target,power,color,size):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.color=color;d.shape='DISK';d.size=size
    o=bpy.data.objects.new(name,d);groups['Lighting'].objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
area('Key | warm industrial rim',layout(-2,4,7),layout(0,0),210,(1,.64,.36),6)
area('Fill | human hull',layout(-3,1,6),ship.location,130,(.37,.57,1),5)
area('Fill | jade carapace',layout(3,2,6),alien.location,170,(.6,.85,.72),5)

# Validate separate ships, socket ownership and analytic shield contacts.
bpy.context.view_layer.update()
assert (ship.location-alien.location).length>5
for collection,owner in [('HumanEquipment',ship),('AlienFrigate',alien)]:
    assert all(o.parent==owner for o in groups[collection].objects if o!=owner)
assert not any('landing foot' in o.name or 'landing strut' in o.name or 'Mining rig' in o.name for o in scene.objects)
assert 'Station' not in bpy.data.collections and 'Cruiser' not in bpy.data.collections
scene['description']='Starter frigate dueling a Veyr alien frigate; two readable factions, pulse fire, plasma and shield impacts.'
scene['seed']=2268;scene['opponent_faction']='Veyr (working visual concept)'
scene.render.engine='CYCLES';scene.cycles.samples=int(os.environ.get('RENDER_SAMPLES','64'));scene.cycles.use_denoising=bool(getattr(bpy.app.build_options,'openimagedenoise',False))
scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=int(os.environ.get('RENDER_SCALE','100'))
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(OUT/'frigate_combat_preview.png');scene.view_settings.view_transform='AgX'
scene.use_nodes=True;n=scene.node_tree.nodes;n.clear();l=scene.node_tree.links
rl=n.new('CompositorNodeRLayers');gl=n.new('CompositorNodeGlare');gl.glare_type='FOG_GLOW';gl.quality='HIGH';gl.threshold=1.4;gl.size=7;output=n.new('CompositorNodeComposite');l.new(rl.outputs['Image'],gl.inputs[0]);l.new(gl.outputs[0],output.inputs[0])
bpy.ops.object.select_all(action='DESELECT')
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':a.spaces.active.region_3d.view_perspective='CAMERA';a.spaces.active.overlay.show_overlays=False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'frigate_combat.blend'),compress=True)
exports={'human_combat_frigate':['Frigate','HumanEquipment'],'veyr_frigate':['AlienFrigate'],'battle_effects':['BattleEffects'],'asteroid_field':['AsteroidField']};stats={}
for name,collections in exports.items():
    bpy.ops.object.select_all(action='DESELECT')
    for collection in collections:
        for o in groups[collection].objects:o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(OUT/(name+'.glb')),export_format='GLB',use_selection=True,export_apply=True,export_yup=True)
    raw=(OUT/(name+'.glb')).read_bytes();length=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+length])
    stats[name]={'triangles':sum(g['accessors'][p['indices']]['count']//3 for m in g.get('meshes',[]) for p in m['primitives'])}
bpy.ops.object.select_all(action='DESELECT')
manifest={'seed':2268,'units':'metres','blender_up':'+Z','gltf_up':'+Y','ship_forward':'+Y','source':'starter_frigate_source.blend / Frigate collection','assets':stats,'opponent':{'faction':'Veyr','status':'working visual concept','class':'frigate'},'combat':{'root_separation':(ship.location-alien.location).length,'human_weapon_emitter':list(human_muzzle),'alien_shield_hit':list(alien_hit),'alien_emitters':[list(p) for p in enemy_emitters],'human_shield_hits':[list(p) for p,n in human_hits],'human_shield_radii':list(human_radii),'alien_shield_radii':list(alien_radii),'shield_contacts_validated':3},'presentation':'Static combat vignette. Shield patches, pulse bolts and drive plumes are separate meshes; AI, damage and combat simulation are not implemented.'}
(OUT/'scene_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('COMBAT_VALIDATION_OK',json.dumps(manifest['combat']),flush=True)
if not os.environ.get('SKIP_RENDER'):bpy.ops.render.render(write_still=True)
print('COMBAT_SCENE_COMPLETE',str(OUT),flush=True)
