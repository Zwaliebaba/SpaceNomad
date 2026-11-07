"""Space Nomad original depot study. Run with Blender 4.3+ in background mode.

blender --background --python create_frontier_depot.py -- --render
Outputs are written next to this script. No third-party assets or add-ons.
"""
import argparse
import json
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector

OUT = Path(__file__).resolve().parent
random.seed(419)
args = argparse.ArgumentParser()
args.add_argument('--render', action='store_true')
args.add_argument('--all-views', action='store_true')
opts = args.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for coll in list(bpy.data.collections):
    if coll.name != 'Collection':
        bpy.data.collections.remove(coll)
base = bpy.data.collections.get('Collection')
base.name = '01_Station'
collections = {'station': base}
for key, name in [('rock', '02_Asteroid'), ('ship', '03_Player_Ship'),
                  ('salvage', '04_Salvage'), ('background', '05_Backdrop'),
                  ('anchors', '06_Interaction_Anchors'), ('lights', '07_Lighting'),
                  ('cameras', '08_Cameras')]:
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    collections[key] = coll
active_group = 'station'


def group(obj, key=None):
    for coll in list(obj.users_collection):
        coll.objects.unlink(obj)
    collections[key or active_group].objects.link(obj)
    return obj


def color(hex_value):
    vals = [int(hex_value[i:i+2], 16) / 255 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in vals)


def material(name, hex_value, metal=0, rough=.65, emission=0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    rgba = (*color(hex_value), 1)
    m.diffuse_color = rgba
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = rgba
    p.inputs['Metallic'].default_value = metal
    p.inputs['Roughness'].default_value = rough
    if emission:
        p.inputs['Emission Color'].default_value = rgba
        p.inputs['Emission Strength'].default_value = emission
    return m


steel = material('Hull | slate steel', '747D90', .45)
lightsteel = material('Hull | pale edge', 'A4A7B1', .3)
dark = material('Structure | midnight', '293846', .4)
deck = material('Deck | graphite', '505967', .3)
amber = material('Safety | ochre', 'FFB52E', .2)
rust = material('Identity | vermilion', 'B74735', .15)
ivory = material('Ship | ivory', 'DBDED9', .2)
olive = material('Cargo | olive', '69765A', .1)
window = material('Emission | amber', 'FF8A24', emission=5)
cyan = material('Emission | navigation cyan', '62E8F0', emission=4)
glass = material('Canopy | blue black', '102D43', .55, .22)
rocks = [material('Rock | facet %02d' % i, h) for i, h in enumerate(
    ['696075', '756B80', '82778C', '574E63', '62596D'])]


def finish(obj, name, mat, key=None):
    obj.name = name
    if mat:
        obj.data.materials.append(mat)
    return group(obj, key)


def box(name, loc, size, mat, bevel=.04):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = finish(bpy.context.object, name, mat)
    o.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = o.modifiers.new('Machined edge', 'BEVEL')
        mod.width = bevel
        mod.segments = 1
    return o


def cylinder(name, loc, radius, depth, mat, vertices=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    return finish(bpy.context.object, name, mat)


def beam(name, a, b, width, mat):
    a, b = Vector(a), Vector(b)
    o = box(name, (a+b)/2, (width, width, (b-a).length), mat, .015)
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = (b-a).to_track_quat('Z', 'Y')
    return o


def ico(name, loc, size, mat=None, sub=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=1, location=loc)
    o = finish(bpy.context.object, name, mat)
    for v in o.data.vertices:
        v.co *= random.uniform(.86, 1.13)
    o.scale = size
    if mat is None:
        for m in rocks:
            o.data.materials.append(m)
        for p in o.data.polygons:
            p.material_index = random.randrange(len(rocks))
    return o


def arc(name, center, r0, r1, start, end, mat, steps=8, plane='XY'):
    verts = []
    for i in range(steps+1):
        t = start + (end-start)*i/steps
        for r in (r0, r1):
            v = (r*math.cos(t), r*math.sin(t), 0) if plane == 'XY' else (r*math.cos(t), 0, r*math.sin(t))
            verts.append(tuple(Vector(center)+Vector(v)))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], [(2*i, 2*i+1, 2*i+3, 2*i+2) for i in range(steps)])
    mesh.update()
    o = bpy.data.objects.new(name, mesh)
    collections[active_group].objects.link(o)
    o.data.materials.append(mat)
    return o


def rail(a, b, posts=7):
    a, b = Vector(a), Vector(b)
    for i in range(posts):
        p = a.lerp(b, i/(posts-1))
        beam('Rail | upright', p, p+Vector((0,0,.85)), .07, amber)
    for h in (.35, .85):
        beam('Rail | horizontal', a+Vector((0,0,h)), b+Vector((0,0,h)), .055, amber)


def beacon(loc):
    x,y,z = loc
    cylinder('Beacon | foot', (x,y,z+.08), .16, .16, dark)
    cylinder('Beacon | stem', (x,y,z+.3), .055, .4, steel)
    cylinder('Beacon | lantern', (x,y,z+.57), .11, .2, window, 8)


# Complete volume, not a front-facing backdrop.
active_group = 'rock'
ico('Asteroid | primary mass', (2,6,1), (10,7.5,8), sub=3)
ico('Asteroid | port shoulder', (-5,4,-1), (5,5,5), sub=2)
ico('Asteroid | rear outcrop', (5,10,-2), (6,5,5), sub=2)
# Cut a real recess so the hangar interior remains open from every angle.
cutter=box('Temporary hangar excavation',(3,0,2.5),(6,6,4.6),None,0)
for rock in list(collections['rock'].objects):
    if rock != cutter:
        bpy.context.view_layer.objects.active=rock
        mod=rock.modifiers.new('Excavated hangar cavity','BOOLEAN')
        mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
        bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.data.objects.remove(cutter,do_unlink=True)
active_group = 'station'
box('Dock | structural slab', (0,-5,-.45), (16,12,.9), dark, .18)
for x in (-6,-2,2,6):
    for y in (-9,-5,-1):
        box('Dock | deck panel', (x,y,.015), (3.91,3.91,.12), deck)
box('Dock | front fascia', (0,-11,-.35), (16,.18,.4), steel)
for x in (-6,0,6):
    beam('Dock | lower diagonal', (x,-10,-.9), (x,2,-5), .55, rust)
    beam('Dock | longitudinal girder', (x,-10,-1.0), (x,3,-1.0), .4, steel)
for y in (-8,-4,0):
    beam('Dock | cross brace', (-7,y,-1.0), (7,y,-1.0), .3, dark)
rail((-8,-10.8,.12), (-8,.2,.12), 9)
rail((8,-10.8,.12), (8,.2,.12), 9)
rail((-7.9,-11,.12), (-3,-11,.12), 5)
rail((3,-11,.12), (7.9,-11,.12), 5)
for x in (-7.8,-3,3,7.8):
    beacon((x,-10.9,.15))
for x in (-7.8,7.8):
    for y in (-7,-3,0):
        beacon((x,y,.15))
for i in range(12):
    arc('Dock | segmented landing paint', (-2,-6,.085), 2.5,2.72, i*math.tau/12, (i+.74)*math.tau/12, amber, 3)
box('Dock | pad center bar', (-2,-6,.09), (.12,1.5,.015), ivory, 0)
for y in (-3.2,-2.1,-1):
    box('Dock | approach marking', (2,y,.09), (.12,.65,.015), amber, 0)

# A recessed hangar with floor, side walls, segmented frame, and overhead canopy.
box('Hangar | foundation', (3,.6,.25), (8,4,.45), steel)
box('Hangar | interior back', (3,2,2.5), (6,.3,4.6), dark)
box('Hangar | ceiling', (3,.4,4.9), (7,4,.6), steel, .18)
for x in (-.5,6.5):
    box('Hangar | buttress', (x,-.3,2.35), (1.0,2.8,4.6), steel, .18)
    box('Hangar | vertical beacon', (x,-1.73,2.1), (.15,.06,1.9), window, .01)
box('Hangar | lintel', (3,-1,4.65), (7.8,1.4,.85), steel, .22)
box('Hangar | entrance light', (3,-1.73,4.6), (3.0,.08,.2), window)
for x in (.4,5.6):
    beam('Hangar | inner orange frame', (x,-1.3,.45), (x,-1.3,4.05), .16, amber)
beam('Hangar | frame top', (.4,-1.3,4.05), (5.6,-1.3,4.05), .16, amber)
for i in range(5):
    box('Hangar | roof vent', (1+i,-.1,5.25), (.22,1.2,.16), dark)
box('Habitation | port module', (-4,1.4,2), (4,3.2,3.8), steel, .22)
box('Habitation | port cap', (-4,1.4,4), (4.4,3.5,.35), dark)
box('Habitation | starboard module', (8,1.2,2), (2.7,3.5,3.8), steel, .18)
for x in (-5.3,-4,-2.7,7.3,8.4):
    box('Habitation | front window', (x,-.245,2.5), (.9,.045,.8), window, .02)


def tower(name, x,y,base_z,height,radius):
    cylinder(name+' | drum', (x,y,base_z+height/2), radius,height,steel,8)
    cylinder(name+' | lower collar', (x,y,base_z+.15), radius*1.13,.3,dark,8)
    cylinder(name+' | glowing clerestory', (x,y,base_z+height-.45), radius*1.015,.65,window,8)
    for t in range(8):
        a = t*math.tau/8
        beam(name+' | window mullion', (x+math.cos(a)*radius,y+math.sin(a)*radius,base_z+height-.85),
             (x+math.cos(a)*radius,y+math.sin(a)*radius,base_z+height), .1,dark)
    bpy.ops.mesh.primitive_cone_add(vertices=8,radius1=radius*1.3,radius2=radius*.7,depth=.65,location=(x,y,base_z+height+.3))
    finish(bpy.context.object,name+' | cap',steel)
    beam(name+' | aerial',(x,y,base_z+height+.65),(x,y,base_z+height+2.3),.07,dark)
    beacon((x,y,base_z+height+2.3))


tower('Operations', -4,2,4.2,4.2,1.35)
tower('Lookout', 7,4,5.9,2.8,1.2)
# Upper equipment shelf and a geometric parabolic antenna.
box('Operations | upper equipment shelf', (1.4,3,9.1), (5,3,.5), dark)
cylinder('Dish | mounting pedestal',(1.4,3,9.8),.5,1.4,steel)
verts, faces = [(0,0,0)], []
for i in range(24):
    a = i*math.tau/24
    verts.append((1.45*math.cos(a),1.45*math.sin(a),.5))
for i in range(24):
    faces.append((0,1+i,1+(i+1)%24))
mesh=bpy.data.meshes.new('Dish | faceted bowl')
mesh.from_pydata(verts,[],faces)
mesh.update()
dish=bpy.data.objects.new('Dish | faceted bowl',mesh)
collections['station'].objects.link(dish)
dish.data.materials.append(lightsteel)
dish.location=(1.4,3,10.6)
dish.rotation_euler=(math.radians(32),math.radians(-18),0)
axis=dish.rotation_euler.to_quaternion() @ Vector((0,0,1.8))
tip=Vector(dish.location)+axis
beam('Dish | feed mast',dish.location,tip,.065,dark)
ico('Dish | receiver',tip,(.14,.14,.14),cyan)

# Rear geometry provides an intentional orbit silhouette.
box('Rear | service module',(2,12.5,0),(6,3.5,3),steel,.2)
for x in (0,2,4):
    cylinder('Rear | tank',(x,13.4,2.2),.65,2.2,dark)
    box('Rear | window',(x,14.28,.5),(1,.06,.4),window)
for x in (-6,7):
    beam('Utility | trunk',(x,0,-1),(x,0,-3.3),.35,rust)
    beam('Utility | return',(x,0,-3.3),(x,5,-3.3),.35,rust)

# Cargo and awning.
for i,(x,y,z,s) in enumerate([(-5,-1,.8,1.3),(-6.3,-1,.65,1.0),(-5,-1,2.0,1.0),
                            (6,-5,.7,1.1),(6,-3.6,.7,1.1),(6,-4.4,1.8,.9),
                            (1,.8,.9,1.2),(3,1,.7,.9),(4,.6,.65,.8)]):
    box('Cargo | crate %02d'%i,(x,y,z),(s,s,s),olive if i%2 else rust)
    for dx in (-.32,.32):
        box('Cargo | binding',(x+dx*s,y,z),(s*.06,s*1.015,s*1.015),dark,.005)
for x in (-6.5,-2):
    beam('Awning | pole',(x,-2,.1),(x,-2,3.1),.07,dark)
mesh=bpy.data.meshes.new('Awning | fabric')
mesh.from_pydata([(-6.5,-2,3.1),(-2,-2,3.1),(-2,0,3.5),(-6.5,0,3.5),(-4.25,-2,2.85)],[],[(0,4,3),(4,2,3),(4,1,2)])
mesh.update()
awning=bpy.data.objects.new('Awning | vermilion fabric',mesh)
collections['station'].objects.link(awning)
awning.data.materials.append(rust)
mod=awning.modifiers.new('Fabric thickness','SOLIDIFY');mod.thickness=.025

# Crane with A-frame, boom, suspended grapple and visible mechanical joints.
cylinder('Crane | base',(-8,1,1),.8,1.6,dark)
beam('Crane | mast',(-8,1,1),(-8,1,6.5),.5,amber)
beam('Crane | boom',(-8,1,6.3),(-13,-.2,6.0),.45,amber)
beam('Crane | upper brace',(-8,1,7.1),(-13,-.2,6),.12,dark)
beam('Crane | backstay',(-8,1,7.1),(-6.9,1,4.8),.12,dark)
beam('Crane | cable',(-13,-.2,6),(-13,-.2,2.8),.035,dark)
cylinder('Crane | grapple hub',(-13,-.2,2.6),.3,.4,amber,8)
for i in range(3):
    a=i*math.tau/3
    p=(-13+math.cos(a)*.7,-.2+math.sin(a)*.7,2.0)
    beam('Crane | claw',(-13,-.2,2.6),p,.12,amber)
    beam('Crane | claw tip',p,(-13+math.cos(a)*.35,-.2+math.sin(a)*.35,1.7),.1,dark)

active_group='salvage'
arc('Salvage | broken ring',(-17,5,2),2.6,3.3,.15,5.2,steel,18,'XZ')
ring=bpy.data.objects['Salvage | broken ring']
solid=ring.modifiers.new('Ring thickness','SOLIDIFY');solid.thickness=.6
for i in range(7):
    a=.15+i*.7
    o=box('Salvage | ring rib',(-17+2.95*math.cos(a),4.95,2+2.95*math.sin(a)),(.4,.85,.5),dark)
    o.rotation_euler[1]=-a
for i in range(9):
    loc=(-17+random.uniform(-5,4),random.uniform(-2,10),random.uniform(-5,2))
    o=box('Salvage | hull fragment',loc,(random.uniform(.7,2),random.uniform(.4,1.1),.3),steel)
    o.rotation_euler=(random.random(),random.random(),random.random()*3)
for i in range(12):
    s=random.uniform(.2,.75)
    ico('Salvage | drifting rock',(-17+random.uniform(-7,5),random.uniform(-3,13),random.uniform(-6,6)),(s,s*.8,s*.9))

active_group='ship'
box('Nomad | hull',(0,0,0),(2.2,4.6,.85),ivory,.25)
box('Nomad | raised spine',(0,-.05,.65),(1.1,2.5,.65),rust,.16)
box('Nomad | cockpit',(0,-1.6,.55),(1.35,1,.35),glass,.16)
for x in (-1.4,1.4):
    box('Nomad | nacelle',(x,.2,-.05),(.8,3.3,.8),ivory,.15)
    box('Nomad | nacelle stripe',(x,.3,.4),(.55,1.8,.07),rust)
    o=cylinder('Nomad | engine shroud',(x,1.9,-.05),.34,.5,dark)
    o.rotation_euler[0]=math.pi/2
    o=cylinder('Nomad | engine glow',(x,2.17,-.05),.25,.06,cyan)
    o.rotation_euler[0]=math.pi/2
    beam('Nomad | lower skid',(x,-.6,-.6),(x,1.1,-.6),.12,dark)
bpy.ops.object.empty_add(type='PLAIN_AXES',location=(-5,-14,2))
ship_root=finish(bpy.context.object,'Nomad_Mk_I | assembly',None)
ship_root.rotation_euler[2]=math.radians(-28)
for o in list(collections['ship'].objects):
    if o != ship_root:
        o.parent=ship_root

active_group='background'
blue=material('Planet | ocean','1B4778',rough=1)
land=material('Planet | continents','416A74',rough=1)
planet=ico('Backdrop | distant planet',(-45,48,14),(16,16,16),blue,sub=3)
planet.data.materials.append(land)
for f in planet.data.polygons:
    c=f.center
    f.material_index=1 if math.sin(c.x*9+c.z*4)+math.cos(c.y*8-c.z*3)>.8 else 0
star=material('Backdrop | star','B0D4E8',emission=1.5)
for i in range(95):
    s=random.uniform(.035,.09)
    ico('Backdrop | star', (random.uniform(-65,65),random.uniform(55,90),random.uniform(-20,60)),(s,s,s),star)

active_group='anchors'
for hid,label,loc in [('dock','Docking Platform',(-2,-6,.4)),('depot','Depot Entrance',(3,-1,2.5)),
                      ('ops','Station Operations',(-4,2,9)),('salvage','Salvage Field',(-17,5,3))]:
    bpy.ops.object.empty_add(type='SPHERE',radius=.35,location=loc)
    o=finish(bpy.context.object,'HOTSPOT_'+hid,None)
    o['hotspot_id']=hid
    o['display_name']=label
    o['intent']='Visual anchor only; gameplay requires server validation.'

active_group='lights'
def area(name,loc,target,power,size,col):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=col
    o=bpy.data.objects.new(name,data);collections['lights'].objects.link(o);o.location=loc
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    return o

area('Key | cool starlight',(-12,-15,25),(0,0,0),5500,18,(.64,.78,1))
area('Fill | blue bounce',(18,-2,12),(0,0,0),3800,14,(.38,.59,1))
area('Rim | rear cool',(-3,17,20),(0,3,0),6500,12,(.7,.65,1))
area('Dock | warm practical',(3,-2,4),(2,-6,0),420,5,(1,.42,.12))
area('Hangar | interior practical',(3,.5,4),(3,.2,0),280,3,(1,.52,.2))
area('Ship | cyan engine fill',(-5,-11,2),(-5,-14,2),90,2,(.1,.8,1))
world=bpy.data.worlds.new('Deep navy space');bpy.context.scene.world=world
world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(*color('071525'),1)
world.node_tree.nodes['Background'].inputs[1].default_value=.35

active_group='cameras'
def camera(name,loc,target,lens=46):
    data=bpy.data.cameras.new(name);data.lens=lens;data.clip_end=500
    o=bpy.data.objects.new(name,data);collections['cameras'].objects.link(o);o.location=loc
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    return o

hero=camera('CAM_Hero',(31,-43,29),(-3,0,2),44)
rear=camera('CAM_Rear',(-29,38,23),(0,1,1),46)
under=camera('CAM_Underside',(24,-34,-19),(0,1,-1),46)
# Place the decorative planet in the hero sky without intersecting the station.
q=hero.rotation_euler.to_quaternion()
planet.location=hero.location+q @ Vector((-58,30,-220))
planet.scale=(25,25,25)
area('Backdrop | planet key',planet.location+q @ Vector((-25,30,50)),planet.location,28000,25,(.5,.7,1))
scene=bpy.context.scene
scene.camera=hero
scene.unit_settings.system='METRIC'
scene['purpose']='Original Space Nomad orbitable location art study; no game implementation.'
scene['reference']='User-supplied Frontier Salvage Depot C2 Interface visual reference.'
scene['camera_requirement']='Free orbit and zoom. Camera collision and UI occlusion are future runtime work.'
scene.render.engine='CYCLES'
scene.cycles.samples=96
# The cloud Blender build omits OpenImageDenoise; do not require it to render.
scene.cycles.use_denoising=False
scene.render.resolution_x=1440
scene.render.resolution_y=960
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'
scene.use_nodes=True
nodes=scene.node_tree.nodes;nodes.clear()
rl=nodes.new('CompositorNodeRLayers')
glow=nodes.new('CompositorNodeGlare');glow.glare_type='FOG_GLOW';glow.quality='MEDIUM';glow.threshold=2
comp=nodes.new('CompositorNodeComposite')
scene.node_tree.links.new(rl.outputs['Image'],glow.inputs['Image'])
scene.node_tree.links.new(glow.outputs['Image'],comp.inputs['Image'])
for screen in bpy.data.screens:
    for area_ui in screen.areas:
        if area_ui.type=='VIEW_3D':
            space=area_ui.spaces.active
            space.region_3d.view_distance=52
            space.region_3d.view_location=(-2,0,1)
            space.region_3d.view_rotation=hero.rotation_euler.to_quaternion()
            space.region_3d.view_perspective='PERSP'
            space.clip_end=500
            space.shading.type='MATERIAL'
            space.overlay.show_extras=False
            space.overlay.show_floor=False
bpy.ops.object.select_all(action='DESELECT')
# Export only authored location geometry and anchors, not the preview backdrop/lights/cameras.
export_objects=[]
for key in ('station','rock','ship','salvage','anchors'):
    for o in collections[key].objects:
        o.select_set(True);export_objects.append(o)
bpy.ops.export_scene.gltf(filepath=str(OUT/'frontier_depot.glb'),export_format='GLB',
    use_selection=True,export_apply=True,export_extras=True,export_cameras=False,export_lights=False)
bpy.ops.object.select_all(action='DESELECT')
scene.render.filepath=str(OUT/'frontier_depot_preview.png')
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'frontier_depot.blend'))
triangles=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in export_objects if o.type=='MESH')
(OUT/'scene-report.json').write_text(json.dumps({
    'blender_version':bpy.app.version_string,'source_mesh_triangles_before_modifiers':triangles,
    'exported_objects':len(export_objects),'hotspots':['dock','depot','ops','salvage'],
    'note':'Counts are art-study diagnostics, not browser draw calls or a performance benchmark.'},indent=2)+'\n')
if opts.render or opts.all_views:
    for cam,suffix in [(hero,'preview')]+([(rear,'rear'),(under,'underside')] if opts.all_views else []):
        scene.camera=cam
        scene.render.filepath=str(OUT/f'frontier_depot_{suffix}.png')
        bpy.ops.render.render(write_still=True)
print('SPACE_NOMAD_SCENE_COMPLETE',str(OUT))
