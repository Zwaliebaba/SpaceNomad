"""Orbital Sector 7: a HUD-free 3D interpretation of the supplied sector image.
Blender 4.3+: blender -b -t 8 --python create_scene.py
Optional: SCENE_OUTPUT, RENDER_SAMPLES, RENDER_SCALE, SKIP_RENDER.
"""
import bpy, bmesh, random, math, os, json, struct
from pathlib import Path
from mathutils import Vector
from math import pi, sin, cos
random.seed(2346)
OUT=Path(os.environ.get('SCENE_OUTPUT',str(Path(__file__).resolve().parent)));OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):bpy.data.collections.remove(c)
scene=bpy.context.scene;scene.unit_settings.system='METRIC'
groups={}
for name in ['BlueStation','RedStation','BlueFleet','RedFleet','Outposts','Asteroids','EdgeAccents','EngineEffects','Backdrop','Lighting','Cameras']:
    c=bpy.data.collections.new(name);scene.collection.children.link(c);groups[name]=c
view=Vector((.43,-.72,.545)).normalized();right=Vector((.858,.513,0)).normalized();up=view.cross(right).normalized()
def layout(x,y,d=0):return right*x+up*y+view*d
def mat(name,col,metal=0,rough=.5,emission=0,alpha=1):
    m=bpy.data.materials.new(name);m.diffuse_color=(*col,alpha);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*col,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    p.inputs['Emission Color'].default_value=(*col,1);p.inputs['Emission Strength'].default_value=emission;p.inputs['Alpha'].default_value=alpha
    if alpha<1:m.surface_render_method='DITHERED'
    return m
blue=mat('Sector | blue hull',(.012,.030,.050),.65,.50)
blue_top=mat('Sector | blue deck plates',(.035,.070,.102),.55,.48)
red=mat('Sector | red hull',(.035,.010,.017),.6,.5)
red_top=mat('Sector | red deck plates',(.070,.018,.025),.55,.5)
graphite=mat('Sector | dark structure',(.008,.016,.023),.6,.6)
amber=mat('Sector | inhabited amber windows',(1,.48,.10),.1,.4,4)
blue_core=mat('Sector | blue drive cores',(.12,.60,1),0,.3,7)
red_core=mat('Sector | red drive cores',(1,.055,.035),0,.3,5)
blue_wire=mat('Sector | blue 3D edge accents',(.12,.45,.78),.2,.4,1.25)
red_wire=mat('Sector | red 3D edge accents',(.85,.085,.10),.2,.4,1.1)
rock_wire=mat('Sector | teal rock edges',(.075,.17,.18),.3,.7,.20)
rocks=[mat('Sector | green basalt %02d'%i,(.011+i*.010,.027+i*.015,.031+i*.016),.12,.9) for i in range(6)]
blue_tail=mat('Sector | blue exhaust haze',(.01,.15,1),0,.7,.8,.07)
red_tail=mat('Sector | red exhaust haze',(1,.015,.02),0,.7,.7,.07)
blue_jet=mat('Sector | blue hot exhaust',(.02,.30,1),0,.5,2,.18)
red_jet=mat('Sector | red hot exhaust',(1,.025,.02),0,.5,1.5,.18)
edge_materials={'blue':blue_wire,'red':red_wire,'rock':rock_wire}
edge_batches={};roots={}
def root(name,group,p=(0,0,0),scale=1,heading=0):
    o=bpy.data.objects.new(name,None);groups[group].objects.link(o);o.location=p;o.scale=(scale,)*3;o.rotation_euler.z=heading;o['assembly_group']=group
    roots[name]=o;bpy.context.view_layer.update();return o
def mesh(name,vs,fs,owner,group,m,edge=None,width=.012):
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update()
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
    o=bpy.data.objects.new(name,me);groups[group].objects.link(o);o.parent=owner;o.data.materials.append(m)
    if edge:
        segments=edge_batches.setdefault((owner.name,edge),[])
        # Store local segments, preserving each assembly's editable root transform.
        for e in me.edges:segments.append((me.vertices[e.vertices[0]].co.copy(),me.vertices[e.vertices[1]].co.copy(),width))
    return o
def box(name,p,s,owner,group,m,edge=None,width=.012,angle=0):
    vs=[]
    for x,y,z in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]:
        x,y=x*s[0]/2,y*s[1]/2;vs.append((p[0]+x*cos(angle)-y*sin(angle),p[1]+x*sin(angle)+y*cos(angle),p[2]+z*s[2]/2))
    fs=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    return mesh(name,vs,fs,owner,group,m,edge,width)
def cyl(name,p,r,h,owner,group,m,edge=None,n=12,r2=None,width=.012):
    r2=r if r2 is None else r2;vs=[]
    for z,radius in [(-h/2,r),(h/2,r2)]:
        vs.extend([(p[0]+cos(2*pi*i/n)*radius,p[1]+sin(2*pi*i/n)*radius,p[2]+z) for i in range(n)])
    fs=[tuple(reversed(range(n))),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,vs,fs,owner,group,m,edge,width)
def beam(name,a,b,r,owner,group,m,edge=None,n=6,width=.009,r2=None):
    a,b=Vector(a),Vector(b);d=b-a;q=d.to_track_quat('Z','Y');r2=r if r2 is None else r2;vs=[]
    for z,radius in [(-d.length/2,r),(d.length/2,r2)]:
        for i in range(n):vs.append(q@Vector((cos(2*pi*i/n)*radius,sin(2*pi*i/n)*radius,z))+(a+b)/2)
    fs=[tuple(reversed(range(n))),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,vs,fs,owner,group,m,edge,width)
def ring(name,r,band,z,h,owner,group,m,edge,n=32):
    vs=[]
    for height,rad in [(z-h/2,r-band/2),(z-h/2,r+band/2),(z+h/2,r-band/2),(z+h/2,r+band/2)]:
        vs.extend([(cos(2*pi*i/n)*rad,sin(2*pi*i/n)*rad,height) for i in range(n)])
    fs=[]
    for i in range(n):
        j=(i+1)%n;fs.extend([(i,j,j+n,i+n),(i+2*n,i+3*n,j+3*n,j+2*n),(i,i+2*n,j+2*n,j),(i+n,j+n,j+3*n,i+3*n)])
    return mesh(name,vs,fs,owner,group,m,edge,.014)

# Large blue ring station: open orbital ring, square tower and lower utility spine.
station=root('BlueRingStation_ROOT','BlueStation',layout(-11.7,.50))
ring('Blue station | segmented orbital ring',4.85,.68,.20,.62,station,'BlueStation',blue,'blue')
cyl('Blue station | octagonal hub',(0,0,0),1.95,.95,station,'BlueStation',blue,'blue',n=12)
cyl('Blue station | upper hub deck',(0,0,.58),1.8,.22,station,'BlueStation',blue_top,'blue',n=12)
for i in range(4):
    a=i*pi/2;dx,dy=cos(a),sin(a)
    box('Blue station | radial spoke',(dx*3.2,dy*3.2,.28),(3.1,.58,.46),station,'BlueStation',blue,'blue',angle=a)
    box('Blue station | ring junction',(dx*4.86,dy*4.86,.20),(1.12,1.10,1.0),station,'BlueStation',blue,'blue',.017,angle=a)
box('Blue station | extended docking bridge',(6.15,0,.12),(2.20,.44,.38),station,'BlueStation',blue,'blue')
box('Blue station | external docking node',(7.35,0,.12),(.72,.72,.68),station,'BlueStation',blue,'blue')
for i in range(8):box('Blue station | tower floor',(0,0,.98+i*.57),(1.35,1.35,.57),station,'BlueStation',blue,'blue',.012)
box('Blue station | tower roof',(0,0,5.38),(1.55,1.55,.14),station,'BlueStation',blue_top,'blue')
beam('Blue station | main antenna',(0,0,5.45),(0,0,8.0),.045,station,'BlueStation',blue_top,'blue')
for z in [5.7,6.25,7.0]:box('Blue station | antenna collar',(0,0,z),(.23,.23,.25),station,'BlueStation',blue,'blue',.009)
cyl('Blue station | antenna beacon',(0,0,8.02),.07,.15,station,'BlueStation',blue_core,n=6)
for z,r,h in [(-.9,1.38,.8),(-1.65,.72,.7),(-2.4,.40,.8),(-3.15,.21,.65),(-3.7,.08,.5)]:
    cyl('Blue station | underslung service tier',(0,0,z),r,h,station,'BlueStation',blue,'blue',n=8,width=.009)
for i in range(32):
    a=2*pi*(i+.5)/32
    if sin(a)<.3 or i%3==0:
        for offset in [-.11,.11]:
            aa=a+offset/4.85;box('Blue station | ring window',(cos(aa)*5.20,sin(aa)*5.20,.23),(.19,.035,.16),station,'BlueStation',amber,angle=a+pi/2)
for a in [pi/2,pi*.75]:
    x,y=cos(a)*4.85,sin(a)*4.85
    box('Blue station | ring utility block',(x,y,.75),(.72,.8,.50),station,'BlueStation',blue,'blue')
    beam('Blue station | ring antenna',(x,y,1.0),(x,y,2.45),.025,station,'BlueStation',blue_top,'blue',width=.006)
    cyl('Blue station | ring beacon',(x,y,2.45),.04,.1,station,'BlueStation',blue_core,n=5)

# Opposing red station uses a compact hub with rectilinear perimeter arms.
enemy=root('RedCommandStation_ROOT','RedStation',layout(19,7,-3),.9)
box('Red station | command hub',(0,0,.20),(1.95,1.95,1.7),enemy,'RedStation',red,'red',.016)
box('Red station | lower collar',(0,0,-.80),(1.4,1.4,.45),enemy,'RedStation',red,'red')
for i in range(4):
    a=i*pi/2;dx,dy=cos(a),sin(a)
    for side in [-1,1]:
        p=Vector((dx*2.0,dy*2.0,.25))+Vector((-dy,dx,0))*side*.45
        box('Red station | perimeter arm',p,(2.4,.22,.25),enemy,'RedStation',red,'red',.012,angle=a)
        end=Vector((dx*3.20,dy*3.20,.25))+Vector((-dy,dx,0))*side*.45
        box('Red station | arm node',end,(.40,.40,.40),enemy,'RedStation',red,'red',.012)
for z,w in [(1.22,.62),(1.8,.40),(2.4,.25),(2.95,.17),(3.5,.11),(4.1,.06)]:
    box('Red station | stepped communications mast',(0,0,z),(w,w,.62),enemy,'RedStation',red,'red',.009)
cyl('Red station | mast beacon',(0,0,4.50),.035,.16,enemy,'RedStation',red_core,n=6)
for z,w in [(-1.35,.72),(-1.9,.40),(-2.3,.14)]:box('Red station | lower spine',(0,0,z),(w,w,.52),enemy,'RedStation',red,'red',.009)

def asteroid(name,owner,group,r=1,stretch=(1,1,1),local=(0,0,0),subdivisions=2,screen_angle=None):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions,radius=r);o=bpy.context.object;o.name=name
    for c in list(o.users_collection):c.objects.unlink(o)
    groups[group].objects.link(o);o.parent=owner;o.location=local
    for v in o.data.vertices:
        p=v.co.copy()*random.uniform(.88,1.12)
        if screen_angle is None:v.co=(p.x*stretch[0],p.y*stretch[1],p.z*stretch[2])
        else:
            u=p.x*stretch[0];w=p.y*stretch[1];a=screen_angle
            v.co=right*(u*cos(a)-w*sin(a))+up*(u*sin(a)+w*cos(a))+view*p.z*stretch[2]
    for m in rocks:o.data.materials.append(m)
    for f in o.data.polygons:f.material_index=random.randrange(6)
    o.data.update()
    segments=edge_batches.setdefault((owner.name,'rock'),[])
    for e in o.data.edges:segments.append((o.data.vertices[e.vertices[0]].co+Vector(local),o.data.vertices[e.vertices[1]].co+Vector(local),.008))
    return o

# Small asteroid installations, with solid rock foundations and attached machinery.
def outpost(name,p,scale=1,team='blue'):
    r=root(name,'Outposts',p,scale);hull=blue if team=='blue' else red;deck=blue_top if team=='blue' else red_top;core=blue_core if team=='blue' else red_core
    asteroid(name+' | foundation',r,'Outposts',1.75,(1.35,1.0,.85),subdivisions=2)
    box(name+' | platform',(0,0,1.30),(3.25,1.80,.35),r,'Outposts',hull,team)
    for x,y,w,d,h in [(-1.0,.20,.48,.6,.65),(0,.28,.65,.72,.45),(.85,.20,.55,.65,.95)]:
        box(name+' | equipment block',(x,y,1.49+h/2),(w,d,h),r,'Outposts',deck,team,.01)
    for x in [-1.2,-.6,0,.6,1.2]:box(name+' | amber equipment window',(x,-.925,1.33),(.12,.025,.12),r,'Outposts',amber)
    box(name+' | service gantry',(-2.05,0,1.30),(1.0,.26,.20),r,'Outposts',hull,team,.009)
    for x,y,top in [(-.98,.20,4.65),(.80,.20,3.0),(.15,.38,2.7)]:
        beam(name+' | antenna',(x,y,1.6),(x,y,top),.026,r,'Outposts',deck,team,width=.007)
        for z in [2.1,2.5]:box(name+' | antenna collar',(x,y,z),(.17,.17,.22),r,'Outposts',hull,team,.007)
        box(name+' | tip beacon',(x,y,top),(.09,.09,.14),r,'Outposts',core)
    return r
outpost('BlueMiningOutpost_A_ROOT',layout(-19,-5.6,.8),1)
outpost('BlueMiningOutpost_B_ROOT',layout(15.5,.2,-1),.73)
outpost('RedListeningOutpost_ROOT',layout(21.2,3.1,-1.8),.48,'red')

# New reference-matched fleet hulls, independent of the earlier frigate designs.
fleet_roots={'blue':[],'red':[]}
def vessel(name,p,scale,team):
    group='BlueFleet' if team=='blue' else 'RedFleet';hull=blue if team=='blue' else red;deck=blue_top if team=='blue' else red_top;core=blue_core if team=='blue' else red_core
    r=root(name,group,p,scale,math.radians(-20));r['faction']=team;r['role']='sector patrol frigate';fleet_roots[team].append(r)
    box(name+' | central keel',(0,0,0),(.48,2.85,.34),r,group,hull,team,.008)
    for side in [-1,1]:
        for y,w in [(-.95,.35),(-.25,.34),(.45,.27),(1.05,.18)]:
            box(name+' | segmented armor',(side*w,y,.07),(.33,.64,.32),r,group,deck,team,.009)
        box(name+' | rear drive pod',(side*.33,-1.34,-.02),(.38,.46,.40),r,group,hull,team,.009)
        box(name+' | drive core',(side*.33,-1.58,-.02),(.24,.028,.23),r,group,core)
        beam(name+' | bright exhaust',(side*.33,-1.60,-.02),(side*.33,-2.65,-.02),.10,r,'EngineEffects',blue_jet if team=='blue' else red_jet,n=10,r2=.002)
        beam(name+' | long exhaust trail',(side*.33,-1.61,-.02),(side*.33,-5.2,-.02),.11,r,'EngineEffects',blue_tail if team=='blue' else red_tail,n=10,r2=.001)
    box(name+' | bridge',(0,.15,.29),(.32,.75,.22),r,group,hull,team,.008)
    return r
for i,(x,y,s) in enumerate([(-.50,.60,1.10),(1.80,-.50,.76),(-4.0,-1.9,.67),(-2.0,-3.0,.50),(3.0,-1.6,.72)]):vessel('BluePatrol_%02d_ROOT'%(i+1),layout(x,y,.7+i*.08),s,'blue')
for i,(x,y,s) in enumerate([(9.30,6.0,.48),(11.5,6.0,.44),(13.6,6.05,.44),(9.10,4.7,.44)]):vessel('RedPatrol_%02d_ROOT'%(i+1),layout(x,y,-1.5+i*.08),s,'red')

hero=root('ForegroundAsteroid_ROOT','Asteroids',layout(14.1,-7.1,4.5))
asteroid('Foreground | large diagonal fractured asteroid',hero,'Asteroids',1,(7.2,3.25,3.0),subdivisions=3,screen_angle=math.radians(21))
field=[(0,9,-8,2.0),(4,10,-10,.35),(6.7,9.4,-9,.20),(4.1,6.5,-6,.40),(-5.5,5.6,-8,.50),(-18,4.4,-6,.25),(-20,2.8,-4,.48),(-13.5,-7.9,-4,.27),(-12.2,-10,-3,.45),(-3.6,-9.2,-3,.65),(3.2,-9.1,-2,.75),(11.5,-1.2,-4,.55),(22,-5.7,-2,.50),(22.3,-3.5,-1,.18)]
for i,(x,y,d,r) in enumerate(field):
    owner=root('SectorAsteroid_%02d_ROOT'%i,'Asteroids',layout(x,y,d));asteroid('Sector | asteroid %02d'%i,owner,'Asteroids',r,(1.15,.85,1.05),subdivisions=2 if r>.3 else 1)

# Batch physical edge tubes per assembly and material, keeping draw counts manageable.
for (owner_name,style),segments in edge_batches.items():
    vs=[];fs=[]
    for a,b,radius in segments:
        a,b=Vector(a),Vector(b);direction=b-a
        if direction.length<.00001:continue
        q=direction.to_track_quat('Z','Y');start=len(vs)
        for end in [a,b]:
            for i in range(4):vs.append(end+q@Vector((cos(i*pi/2)*radius,sin(i*pi/2)*radius,0)))
        fs.extend([(start+i,start+(i+1)%4,start+(i+1)%4+4,start+i+4) for i in range(4)])
    o=mesh(owner_name+' | '+style+' physical edge accents',vs,fs,roots[owner_name],'EdgeAccents',edge_materials[style]);o['purpose']='3D technical edge treatment, not HUD'

# Large faceted planet and a slim atmospheric limb; backdrop-only, no external textures.
planet_root=root('BluePlanet_ROOT','Backdrop',layout(-20.3,4.9,-35))
planet_mats=[mat('Planet | blue facet %02d'%i,(.001+i*.006,.003+i*.017,.008+i*.037),.05,1,.05) for i in range(7)]
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5,radius=11.0);planet=bpy.context.object;planet.name='Backdrop | faceted blue planet'
for c in list(planet.users_collection):c.objects.unlink(planet)
groups['Backdrop'].objects.link(planet);planet.parent=planet_root
for m in planet_mats:planet.data.materials.append(m)
planet_light=(right*.65+up*.75+view*.10).normalized()
for f in planet.data.polygons:
    value=max(0,f.normal.dot(planet_light))**1.7
    f.material_index=max(0,min(6,round(value*6+random.uniform(-.35,.35))))
if hasattr(planet,'visible_shadow'):planet.visible_shadow=False
atmosphere=bpy.data.materials.new('Planet | blue atmospheric limb');atmosphere.use_nodes=True;n=atmosphere.node_tree.nodes;n.clear();l=atmosphere.node_tree.links
output=n.new('ShaderNodeOutputMaterial');mix=n.new('ShaderNodeMixShader');transparent=n.new('ShaderNodeBsdfTransparent');em=n.new('ShaderNodeEmission');em.inputs[0].default_value=(.055,.25,.65,1);em.inputs[1].default_value=2.2
layer=n.new('ShaderNodeLayerWeight');layer.inputs['Blend'].default_value=.25;power=n.new('ShaderNodeMath');power.operation='POWER';power.inputs[1].default_value=3
geometry=n.new('ShaderNodeNewGeometry');dot=n.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT';dot.inputs[1].default_value=planet_light
positive=n.new('ShaderNodeMath');positive.operation='MAXIMUM';positive.inputs[1].default_value=0;mask=n.new('ShaderNodeMath');mask.operation='MULTIPLY'
l.new(geometry.outputs['Normal'],dot.inputs[0]);l.new(dot.outputs['Value'],positive.inputs[0]);l.new(positive.outputs[0],mask.inputs[1])
l.new(layer.outputs['Fresnel'],power.inputs[0]);l.new(power.outputs[0],mask.inputs[0]);front=n.new('ShaderNodeMath');front.operation='SUBTRACT';front.inputs[0].default_value=1;l.new(geometry.outputs['Backfacing'],front.inputs[1]);visible=n.new('ShaderNodeMath');visible.operation='MULTIPLY';l.new(front.outputs[0],visible.inputs[0]);l.new(mask.outputs[0],visible.inputs[1]);l.new(visible.outputs[0],mix.inputs[0]);l.new(transparent.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],output.inputs[0])
bpy.ops.mesh.primitive_uv_sphere_add(segments=96,ring_count=48,radius=11.07);o=bpy.context.object;o.name='Backdrop | blue atmosphere'
for c in list(o.users_collection):c.objects.unlink(o)
groups['Backdrop'].objects.link(o);o.parent=planet_root;o.data.materials.append(atmosphere)
for f in o.data.polygons:f.use_smooth=True
if hasattr(o,'visible_shadow'):o.visible_shadow=False
back=root('Starfield_ROOT','Backdrop',layout(0,0,-80))
background=mat('Space | blue black',(.0015,.003,.006),0,1,1)
box('Backdrop | deep space',(0,0,0),(160,120,.1),back,'Backdrop',background)
back.rotation_euler=view.to_track_quat('Z','Y').to_euler()
star_root=root('Stars_ROOT','Backdrop')
stars=mat('Space | quiet stars',(.42,.62,.8),0,1,2);vs=[];fs=[]
for i in range(850):
    p=layout(random.uniform(-32,32),random.uniform(-20,20),-65);r=random.choices([.007,.012,.020],[7,3,1])[0];j=len(vs)
    vs.extend([p-right*r-up*r,p+right*r-up*r,p+right*r+up*r,p-right*r+up*r]);fs.append((j,j+1,j+2,j+3))
mesh('Backdrop | sparse starfield',vs,fs,star_root,'Backdrop',stars)

world=bpy.data.worlds.new('Sector | deep space');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.025,.045,.075,1);world.node_tree.nodes['Background'].inputs[1].default_value=.18;scene.world=world
d=bpy.data.lights.new('Sector | cool starlight','SUN');d.energy=2.3;d.angle=.12;d.color=(.65,.80,1)
o=bpy.data.objects.new(d.name,d);groups['Lighting'].objects.link(o);o.rotation_euler=(.4,-.7,-.55)
def area(name,p,target,power,color,size):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.color=color;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);groups['Lighting'].objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
area('Sector | broad blue fill',layout(-8,4,24),station.location,1900,(.28,.52,1),20)
area('Sector | green asteroid rim',layout(15,5,20),hero.location,1500,(.62,.82,.66),15)
bpy.ops.object.camera_add(location=layout(0,0,80));camera=bpy.context.object;camera.name='Camera | orbital sector overview'
for c in list(camera.users_collection):c.objects.unlink(camera)
groups['Cameras'].objects.link(camera);camera.rotation_euler=(-view).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=48;camera.data.clip_end=300;scene.camera=camera
scene['description']='Orbital Sector 7 reference scene: blue ring station, five blue ships, four red ships, three asteroid outposts, faceted planet and asteroid field. No HUD or tactical overlays.'
scene['seed']=2346;scene['hud_included']=False
scene.render.engine='CYCLES';scene.cycles.samples=int(os.environ.get('RENDER_SAMPLES','64'));scene.cycles.use_denoising=bool(getattr(bpy.app.build_options,'openimagedenoise',False))
scene.render.resolution_x=1672;scene.render.resolution_y=940;scene.render.resolution_percentage=int(os.environ.get('RENDER_SCALE','100'))
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(OUT/'orbital_sector_7_preview.png');scene.view_settings.view_transform='AgX'
scene.use_nodes=True;n=scene.node_tree.nodes;n.clear();l=scene.node_tree.links
rl=n.new('CompositorNodeRLayers');gl=n.new('CompositorNodeGlare');gl.glare_type='FOG_GLOW';gl.quality='HIGH';gl.threshold=1.8;gl.size=7;output=n.new('CompositorNodeComposite');l.new(rl.outputs['Image'],gl.inputs[0]);l.new(gl.outputs[0],output.inputs[0])
bpy.ops.object.select_all(action='DESELECT')
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':a.spaces.active.region_3d.view_perspective='CAMERA';a.spaces.active.overlay.show_overlays=False
assert len(fleet_roots['blue'])==5 and len(fleet_roots['red'])==4
assert len([o for o in groups['Outposts'].objects if o.type=='EMPTY'])==3
assert not any(o.type=='FONT' for o in scene.objects)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'orbital_sector_7.blend'),compress=True)
exports={'blue_ring_station':['BlueStation'],'red_command_station':['RedStation'],'blue_fleet':['BlueFleet'],'red_fleet':['RedFleet'],'asteroid_outposts':['Outposts'],'asteroid_field':['Asteroids'],'engine_effects':['EngineEffects']};stats={}
for name,collections in exports.items():
    bpy.ops.object.select_all(action='DESELECT');chosen_roots=set()
    for group in collections:
        for o in groups[group].objects:
            o.select_set(True)
            if o.type=='EMPTY':chosen_roots.add(o)
    for o in groups['EdgeAccents'].objects:
        if o.parent in chosen_roots:o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(OUT/(name+'.glb')),export_format='GLB',use_selection=True,export_apply=True,export_yup=True)
    raw=(OUT/(name+'.glb')).read_bytes();length=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+length]);stats[name]={'triangles':sum(g['accessors'][p['indices']]['count']//3 for m in g.get('meshes',[]) for p in m['primitives'])}
bpy.ops.object.select_all(action='DESELECT')
manifest={'seed':2346,'units':'metres (working scene scale)','blender_up':'+Z','gltf_up':'+Y','ship_forward':'+Y','camera':'orthographic / 48 units wide','assets':stats,'composition':{'blue_patrols':5,'red_patrols':4,'asteroid_outposts':3,'main_stations':2,'foreground_asteroid':'ForegroundAsteroid_ROOT','blue_planet':'BluePlanet_ROOT'},'hud_included':False,'excluded_overlays':['menus','fleet list','health bars','resources','minimap','selection cards','selection rings','waypoint marker','dashed course line'],'edge_treatment':'physical edge tubes batched per assembly and color; included with corresponding GLBs','notes':'Independent reference-inspired scene, not a modification of earlier scenes. Planet, starfield, camera and lights are Blender presentation assets. Fleet movement and tactical HUD are not implemented.'}
(OUT/'scene_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('SECTOR_VALIDATION_OK',json.dumps(manifest['composition']),flush=True)
if not os.environ.get('SKIP_RENDER'):bpy.ops.render.render(write_still=True)
print('SECTOR_SCENE_COMPLETE',str(OUT),flush=True)
