#!/usr/bin/env python3

# https://github.com/microsoft/pylance-release/issues/5457
# pyright: reportInvalidTypeForm=false

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import os
import json
import platform
from pathlib import Path
from itertools import *
from importlib import resources

import bpy
import numpy as np
from PIL import Image
from bpy.props import StringProperty, EnumProperty, FloatProperty
from bpy_extras.io_utils import ImportHelper, orientation_helper
import mathutils
from kaitaistruct import KaitaiStream
from .kaitaidefs.srt import Srt

from . import trackmeta

class SONICR_OP_ImportTrk(bpy.types.Operator, ImportHelper):
    bl_idname = "sonicr.import_trk"
    bl_label = "Import Sonic R Track"
    bl_options = {'REGISTER', 'UNDO'}
    filename_ext = ".bin"

    filter_glob: StringProperty(
        default="*.bin;*.srt",
        options={'HIDDEN'},
    )

    scale: FloatProperty(
        name="Scale",
        min=0.0001,
        max=1.0,
        default=0.01,
    )

    trk_items = [
        ("auto",    "Auto-detect",      ""),
        ("island",  "Resort Island",    ""),
        ("city",    "Radical City",     ""),
        ("ruin",    "Regal Ruin",       ""),
        ("factory", "Reactive Factory", ""),
        ("emerald", "Radiant Emerald",  ""),
        ("option3", "Menu Icons",       ""),
        ("title3",  "Title Screen",     "")
    ]

    trk: EnumProperty(
        name="Track",
        items=trk_items
    )

    weather_items = [
        ("none", "None", ""),
        ("clear", "Clear", ""),
        ("rain", "Rain", ""),
        ("snow", "Snow", ""),
    ]

    weather: EnumProperty(
        name="Weather",
        items=weather_items
    )

    tod_items =  [
        ("none", "None", ""),
        ("day", "Day", ""),
        ("sunset", "Sunset", ""),
        ("night", "Night", ""),
    ]

    tod: EnumProperty(
        name="Time of Day",
        items=tod_items
    )

    def draw(self, context):
        layout = self.layout
        #layout.use_property_split = True
        #layout.use_property_decorate = False  # No animation
        layout.prop(self, 'scale')
        layout.prop(self, 'trk')
        layout.prop(self, 'weather')
        layout.prop(self, 'tod')

    def execute(self, context):
        keywords = self.as_keywords(
            ignore=("axis_forward", "axis_up", "filter_glob", "split_mode")
        )
        return loadTrk(context, **keywords)

def menu_func_import(self, context):
    self.layout.operator(SONICR_OP_ImportTrk.bl_idname, text="Sonic R Track (.bin)")

def register():
    bpy.utils.register_class(SONICR_OP_ImportTrk)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(SONICR_OP_ImportTrk)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()

def loadRawTexture(filepath: str) -> Image.Image | None:
    filesize = os.path.getsize(filepath)

    if filesize == 256*256*3:    # generic tpage
        size = (256, 256)
    elif filesize == 32*224*3:   # FLAKE/PLOP
        size = (32, 224)
    elif filesize == 320*384*3:  # .PLY floormap tiles
        size = (320, 384)
    elif filesize == 1664*128*3: # track bg
        size = (1664, 128)
    elif filesize == 640*480*3:  # static bg
        size = (640, 480)
    else:
        return None
    
    # TODO: handle case-sensitive file systems
    with open(filepath, mode='rb') as f:
        image = Image.frombytes('RGB', size, f.read())
    
    # mask out #00FF00
    '''img_array = np.array(image)
    mask_array = \
        (img_array[:,:,0] == 0) & \
        (img_array[:,:,1] == 255) & \
        (img_array[:,:,2] == 0)  
    mask = Image.fromarray(mask_array, '1')
    image.putalpha(mask)'''

    return image

# Create a 1024x1024 texture combining all defined textures as one
# note: 1024x1024 is enough for 16 tpages. that ought to be enough.
def createTextureAtlas(metadata: dict, rootPath: Path, weather: str):
    if weather == "snow":
        textures = metadata['textures_snow']
    else:
        textures = metadata['textures']
    assert(len(textures) <= 16)

    atlas = Image.new('RGBA', (1024, 1024))
    (x, y) = (0, 0)

    def incrPos(x, y):
        x += 256
        if x == 1024:
            x = 0
            y += 256
        return (x, y)

    for path in textures:
        if (path == ""):
            (x, y) = incrPos(x, y)
            continue

        # only supporting 256x256 images for the atlas
        image = loadRawTexture(Path(rootPath) / path)
        assert(image.size == (256, 256))

        atlas.paste(image, (x, y))
        (x, y) = incrPos(x, y)
    
    # convert to Blender image
    bpy_im = bpy.data.images.new("atlas", 1024, 1024)
    # Disable color space calculations
    bpy_im.colorspace_settings.name = 'Non-Color'
    # load data
    bpy_im.pixels = np.divide(np.frombuffer(atlas.tobytes(), dtype=np.uint8).astype(np.float32), 256)
    bpy_im.pack()
    bpy_im.update()
    with bpy.context.temp_override(edit_image=bpy_im):
        bpy.ops.image.flip(use_flip_y=True)


    return bpy_im

''' Generate a material for a given texture '''
def createMaterial(name: str, image, global_color: dict, weather: str, tod: str):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True

    # generated by https://extensions.blender.org/add-ons/node-to-python/
    material = mat.node_tree
    material.color_tag = 'NONE'
    material.description = ""
    material.default_group_node_width = 140
    material.nodes.clear()

    #material interface

    #initialize material nodes
    #node Texture Coordinate
    texture_coordinate = material.nodes.new("ShaderNodeTexCoord")
    texture_coordinate.name = "Texture Coordinate"
    texture_coordinate.from_instancer = False

    #node Light Path
    light_path = material.nodes.new("ShaderNodeLightPath")
    light_path.name = "Light Path"

    #node Emit Only To Camera
    emit_only_to_camera = material.nodes.new("ShaderNodeMixShader")
    emit_only_to_camera.label = "Emit Only To Camera"
    emit_only_to_camera.name = "Emit Only To Camera"

    #node Material Output
    material_output = material.nodes.new("ShaderNodeOutputMaterial")
    material_output.name = "Material Output"
    material_output.is_active_output = True
    material_output.target = 'ALL'
    #Displacement
    material_output.inputs[2].default_value = (0.0, 0.0, 0.0)
    #Thickness
    material_output.inputs[3].default_value = 0.0

    #node Color Attribute
    color_attribute = material.nodes.new("ShaderNodeVertexColor")
    color_attribute.name = "Color Attribute"
    color_attribute.layer_name = ""

    #node Add Vertex Color
    add_vertex_color = material.nodes.new("ShaderNodeVectorMath")
    add_vertex_color.label = "Add Vertex Color"
    add_vertex_color.name = "Add Vertex Color"
    add_vertex_color.operation = 'ADD'

    #node Adjust Vertex Color
    adjust_vertex_color = material.nodes.new("ShaderNodeVectorMath")
    adjust_vertex_color.label = "Adjust Vertex Color"
    adjust_vertex_color.name = "Adjust Vertex Color"
    adjust_vertex_color.operation = 'ADD'
    adjust_vertex_color.inputs[1].default_value = (-0.5, -0.5, -0.5)

    #node Image Texture
    image_texture = material.nodes.new("ShaderNodeTexImage")
    image_texture.name = "Image Texture"
    image_texture.extension = 'REPEAT'
    image_texture.image_user.frame_current = 0
    image_texture.image_user.frame_duration = 1
    image_texture.image_user.frame_offset = 4
    image_texture.image_user.frame_start = 1
    image_texture.image_user.tile = 0
    image_texture.image_user.use_auto_refresh = False
    image_texture.image_user.use_cyclic = False
    image_texture.interpolation = 'Closest'
    image_texture.projection = 'FLAT'
    image_texture.projection_blend = 0.0
    image_texture.image = image

    #node Transparent BSDF
    transparent_bsdf = material.nodes.new("ShaderNodeBsdfTransparent")
    transparent_bsdf.name = "Transparent BSDF"
    #Color
    transparent_bsdf.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0)

    #node Emission
    emission = material.nodes.new("ShaderNodeEmission")
    emission.name = "Emission"
    #Strength
    emission.inputs[1].default_value = 1.0

    #node Mix Alpha
    mix_alpha = material.nodes.new("ShaderNodeMixShader")
    mix_alpha.label = "Mix Alpha"
    mix_alpha.name = "Mix Alpha"

    #node Environment Color
    environment_color = material.nodes.new("ShaderNodeVectorMath")
    environment_color.label = "Environment Color"
    environment_color.name = "Environment Color"
    environment_color.operation = 'ADD'
    if (weather != 'none' and tod != "none" and 'clear' in global_color):
        r = (int(global_color[weather][tod]['r'], 16) - 128) / 256
        g = (int(global_color[weather][tod]['g'], 16) - 128) / 256
        b = (int(global_color[weather][tod]['b'], 16) - 128) / 256
        environment_color.inputs[1].default_value = (r, g, b)
    else:
        environment_color.inputs[1].default_value = (0, 0, 0)

    #Set locations
    texture_coordinate.location = (-752.1420288085938, 172.89166259765625)
    light_path.location = (215.29904174804688, 576.9533081054688)
    emit_only_to_camera.location = (471.49346923828125, 344.90069580078125)
    material_output.location = (703.8551025390625, 367.49798583984375)
    color_attribute.location = (-947.4661865234375, 401.4444274902344)
    add_vertex_color.location = (-252.72947692871094, 380.2495422363281)
    adjust_vertex_color.location = (-703.556640625, 452.8673095703125)
    image_texture.location = (-555.6151123046875, 191.15330505371094)
    transparent_bsdf.location = (-37.10700988769531, 387.06463623046875)
    emission.location = (-38.904380798339844, 288.57635498046875)
    mix_alpha.location = (215.2847900390625, 231.6190643310547)
    environment_color.location = (-476.5963134765625, 448.4853210449219)

    #Set dimensions
    texture_coordinate.width, texture_coordinate.height = 140.0, 100.0
    light_path.width, light_path.height = 140.0, 100.0
    emit_only_to_camera.width, emit_only_to_camera.height = 140.0, 100.0
    material_output.width, material_output.height = 140.0, 100.0
    color_attribute.width, color_attribute.height = 140.0, 100.0
    add_vertex_color.width, add_vertex_color.height = 140.0, 100.0
    adjust_vertex_color.width, adjust_vertex_color.height = 140.0, 100.0
    image_texture.width, image_texture.height = 240.0, 100.0
    transparent_bsdf.width, transparent_bsdf.height = 140.0, 100.0
    emission.width, emission.height = 140.0, 100.0
    mix_alpha.width, mix_alpha.height = 140.0, 100.0
    environment_color.width, environment_color.height = 140.0, 100.0

    #initialize material links
    #light_path.Is Camera Ray -> emit_only_to_camera.Fac
    material.links.new(light_path.outputs[0], emit_only_to_camera.inputs[0])
    #emit_only_to_camera.Shader -> material_output.Surface
    material.links.new(emit_only_to_camera.outputs[0], material_output.inputs[0])
    #texture_coordinate.UV -> image_texture.Vector
    material.links.new(texture_coordinate.outputs[2], image_texture.inputs[0])
    #image_texture.Color -> add_vertex_color.Vector
    material.links.new(image_texture.outputs[0], add_vertex_color.inputs[1])
    #color_attribute.Color -> adjust_vertex_color.Vector
    material.links.new(color_attribute.outputs[0], adjust_vertex_color.inputs[0])
    #add_vertex_color.Vector -> emission.Color
    material.links.new(add_vertex_color.outputs[0], emission.inputs[0])
    #mix_alpha.Shader -> emit_only_to_camera.Shader
    material.links.new(mix_alpha.outputs[0], emit_only_to_camera.inputs[2])
    #image_texture.Alpha -> mix_alpha.Fac
    material.links.new(image_texture.outputs[1], mix_alpha.inputs[0])
    #transparent_bsdf.BSDF -> mix_alpha.Shader
    material.links.new(transparent_bsdf.outputs[0], mix_alpha.inputs[1])
    #emission.Emission -> mix_alpha.Shader
    material.links.new(emission.outputs[0], mix_alpha.inputs[2])
    #adjust_vertex_color.Vector -> environment_color.Vector
    material.links.new(adjust_vertex_color.outputs[0], environment_color.inputs[0])
    #environment_color.Vector -> add_vertex_color.Vector
    material.links.new(environment_color.outputs[0], add_vertex_color.inputs[0])
    
    return mat

# Create required materials
def createAllMaterials(metadata: dict, rootPath: Path, weather: str, tod: str):
    materials = []

    # texture atlas
    atlas = createTextureAtlas(metadata, rootPath, weather)
    materials.append(createMaterial('main', atlas, metadata['global_color'], weather, tod))
    return materials

# Convert a raw tpage/texture coordinate to a position on the texture atlas
def getTextureCoords(tpage: int, x: int, y: int) -> (float, float):
    # convert to float
    (x2, y2) = ((x+1) / 256, (256 - y-1) / 256)

    # the atlas is a 4x4 array of tpages, so compensate
    '''x2 /= 4
    y2 /= 4

    # tpage offset
    x2 += (tpage % 4) / 4
    y2 += (tpage // 4) / 4'''

    return (x2, y2)

def convertTrk(srt: Srt, metadata: dict, filepath: str, scale: float, weather: str, tod: str):
    new_objects = []  # put new objects here
    # TODO: handle case-insensitive file systems
    trkPath = str(Path(metadata['file_trk'].lower()))
    rootPath = str(Path(filepath.lower())).removesuffix(trkPath)

    materials = createAllMaterials(metadata, rootPath, weather, tod)
    
    for i, trkPart in enumerate(srt.trkparts):

        # Track mesh
        me = bpy.data.meshes.new(f"Trk.{i}") 
        ob = bpy.data.objects.new(f"Trk.{i}", me)

        # add all materials to mesh
        for material in materials:
            me.materials.append(material)

        faces = []

        # parse faces (list of tuples of vertex indices)
        for j, f in enumerate(
            zip(
                range(0, len(trkPart.vtxs)),
                range(2, len(trkPart.vtxs)),
                range(3, len(trkPart.vtxs)),
                range(1, len(trkPart.vtxs)),
            )
        ):
            if j % 2 == 1: continue
            faces.append(list(f))

        # to mesh
        face_lengths = list(map(len, faces))

        me.vertices.add(trkPart.num_vtxs)
        me.loops.add(sum(face_lengths))
        me.polygons.add(trkPart.num_faces)
        colormap = ob.data.color_attributes.new(
            name='',
            type='FLOAT_COLOR',
            domain='POINT'
        )

        for src, dst, color in zip(trkPart.vtxs, me.vertices, colormap.data):
            dst.co = mathutils.Vector([
                src.x * -scale,
                src.z * scale,
                src.y * scale
            ])
            color.color = [
                src.r / 256,
                src.g / 256,
                src.b / 256,
                1
            ]

        # set edges/faces
        vertex_indices = list(chain.from_iterable(faces))
        loop_starts = list(islice(chain([0], accumulate(face_lengths)), len(faces)))

        me.polygons.foreach_set("loop_start", loop_starts)
        me.polygons.foreach_set("vertices", vertex_indices)
        
        # no edges - calculate them
        me.update(calc_edges=True)
        me.validate()

        uvtex = me.uv_layers.new()
        j = 0
        for p, f in zip(me.polygons, trkPart.faces):
            # set textures
            uvtex.uv[j+0].vector = getTextureCoords(f.tpage, f.ta_x, f.ta_y)
            uvtex.uv[j+1].vector = getTextureCoords(f.tpage, f.tb_x, f.tb_y)
            uvtex.uv[j+2].vector = getTextureCoords(f.tpage, f.tc_x, f.tc_y)
            uvtex.uv[j+3].vector = getTextureCoords(f.tpage, f.td_x, f.td_y)
            j += 4

        ob.location = mathutils.Vector([
            trkPart.x * -scale,
            trkPart.z * scale,
            trkPart.y * scale
        ])
        
        new_objects.append(ob)

        # Track sub-objects (usually, but not always, rings)
        if len(trkPart.objs) > 1: 
            me = bpy.data.meshes.new(f"Trk.{i}.Objects") 
            ob = bpy.data.objects.new(f"Trk.{i}.Objects", me)
            me.attributes.new(name="objectType", type="INT8", domain="POINT")

            me.vertices.add(len(trkPart.objs) - 1)
            for j, subobj in enumerate(trkPart.objs):
                if subobj.objtype == -1: break
                me.vertices[j].co = mathutils.Vector([
                    subobj.x * -scale,
                    subobj.z * scale,
                    subobj.y * scale
                ])
                me.attributes['objectType'].data[j].value = subobj.objtype

            new_objects.append(ob)
        
    # Decoration parts
    for i, decoPart in enumerate(srt.decoparts):
        # create a new mesh
        me = bpy.data.meshes.new(f"Deco.{i}") 
        ob = bpy.data.objects.new(f"Deco.{i}", me)
        
        # add all materials to mesh
        for material in materials:
            me.materials.append(material)

        # to mesh
        me.vertices.add(decoPart.num_vtxs)
        me.loops.add(3 * decoPart.num_tris + 4 * decoPart.num_quads)
        me.polygons.add(decoPart.num_tris + decoPart.num_quads)
        colormap = ob.data.color_attributes.new(
            name='',
            type='FLOAT_COLOR',
            domain='POINT'
        )

        # vertices
        for src, dst, color in zip(decoPart.vtxs, me.vertices, colormap.data):
            dst.co = mathutils.Vector([
                src.x * -scale,
                src.z * scale,
                src.y * scale
            ])
            color.color = [
                src.r / 256,
                src.g / 256,
                src.b / 256,
                1
            ]

        # triangles
        for j, f in enumerate(decoPart.tris):
            p = me.polygons[j]
            p.loop_start = j * 3
        # quads
        for j, f in enumerate(decoPart.quads):
            p = me.polygons[decoPart.num_tris + j]
            p.loop_start = (decoPart.num_tris * 3) + (j * 4)

        # Face vertices
        # note: cannot set loop_total directly; is derived from loop_start
        for j, f in enumerate(decoPart.tris):
            p = me.polygons[j]
            p.vertices = [f.a, f.b, f.c]
        for j, f in enumerate(decoPart.quads):
            p = me.polygons[decoPart.num_tris + j]
            p.vertices = [f.a, f.b, f.c, f.d]

        # Texture coords
        # must be created after polygons; otherwise Blender crashes
        uvtex = me.uv_layers.new()
        for j, f in enumerate(decoPart.tris):
            uvtex.uv[(j*3)+0].vector = getTextureCoords(f.tpage, f.ta_x, f.ta_y)
            uvtex.uv[(j*3)+1].vector = getTextureCoords(f.tpage, f.tb_x, f.tb_y)
            uvtex.uv[(j*3)+2].vector = getTextureCoords(f.tpage, f.tc_x, f.tc_y)

        for j, f in enumerate(decoPart.quads):
            uvtex.uv[(decoPart.num_tris*3)+(j*4)+0].vector = getTextureCoords(f.tpage, f.ta_x, f.ta_y)
            uvtex.uv[(decoPart.num_tris*3)+(j*4)+1].vector = getTextureCoords(f.tpage, f.tb_x, f.tb_y)
            uvtex.uv[(decoPart.num_tris*3)+(j*4)+2].vector = getTextureCoords(f.tpage, f.tc_x, f.tc_y)
            uvtex.uv[(decoPart.num_tris*3)+(j*4)+3].vector = getTextureCoords(f.tpage, f.td_x, f.td_y)
        
        # no edges - calculate them
        me.update(calc_edges=True)
        me.validate()

        ob.location = mathutils.Vector([
            decoPart.x * -scale,
            decoPart.z * scale,
            decoPart.y * scale
        ])

        new_objects.append(ob)

    # path points
    me = bpy.data.meshes.new("PathPoints") 
    ob = bpy.data.objects.new("PathPoints", me)
    me.vertices.add(srt.num_pathpoints)
    for j, subobj in enumerate(srt.pathpoints):
        me.vertices[j].co = mathutils.Vector([
            subobj.x * -scale,
            subobj.z * scale,
            subobj.y * scale
        ])
    new_objects.append(ob)

    # intro points
    '''me = bpy.data.meshes.new("IntroPoints") 
    ob = bpy.data.objects.new("IntroPoints", me)
    me.vertices.add(srt.num_intropoints)
    for j, subobj in enumerate(srt.intropoints):
        me.vertices[j].co = mathutils.Vector([
            subobj.x * -scale,
            subobj.z * scale,
            subobj.y * scale
        ])
    new_objects.append(ob)'''

    # sec5
    '''me = bpy.data.meshes.new("Sec5") 
    ob = bpy.data.objects.new("Sec5", me)
    me.vertices.add(srt.num_sec5)
    for j, subobj in enumerate(srt.sec5):
        me.vertices[j].co = mathutils.Vector([
            subobj.x * -scale,
            subobj.z * scale,
            subobj.y * scale
        ])
    new_objects.append(ob)'''

    # main path points
    me = bpy.data.meshes.new("MainPathPoints") 
    ob = bpy.data.objects.new("MainPathPoints", me)
    me.vertices.add(srt.num_mainpoints)
    for j, subobj in enumerate(srt.mainpoints):
        me.vertices[j].co = mathutils.Vector([
            subobj.x * -scale,
            subobj.z * scale,
            subobj.y * scale
        ])
    new_objects.append(ob)

    # player spawn points
    me = bpy.data.meshes.new("SpawnPoints") 
    ob = bpy.data.objects.new("SpawnPoints", me)
    spawnpoints = [
        srt.playerpos.p1_end,
        srt.playerpos.p2_end,
        srt.playerpos.p3_end,
        srt.playerpos.p4_end,
        srt.playerpos.p5_end,
        srt.playerpos.p1_start,
        srt.playerpos.p2_start,
        srt.playerpos.p3_start,
        srt.playerpos.p4_start,
        srt.playerpos.p5_start,
        srt.playerpos.tt_end
    ]
    me.vertices.add(len(spawnpoints))
    for j, subobj in enumerate(spawnpoints):
        me.vertices[j].co = mathutils.Vector([
            subobj.x * -scale,
            subobj.z * scale,
            subobj.y * scale
        ])
    new_objects.append(ob)

    # replay camera points
    me = bpy.data.meshes.new("ReplayCamPoints") 
    ob = bpy.data.objects.new("ReplayCamPoints", me)
    me.vertices.add(srt.num_replaypos)
    for j, subobj in enumerate(srt.replaypos):
        me.vertices[j].co = mathutils.Vector([
            subobj.x * -scale,
            subobj.z * scale,
            subobj.y * scale
        ])
    new_objects.append(ob)

    # excluding Sec9 for now

    # floormap
    '''
    if weather == "snow":
        floor_image = makeImage("FloorMap", str(rootPath.joinpath(metadata['floormap']['image_snow'])))
    else:
        floor_image = makeImage("FloorMap", str(rootPath.joinpath(metadata['floormap']['image'])))

    floor_material = makeMaterial("FloorMap", floor_image, metadata['global_color'], weather, tod)
    me = bpy.data.meshes.new("FloorMap") 
    ob = bpy.data.objects.new("FloorMap", me)

    me.materials.append(floor_material)
    me.vertices.add(4)
    me.loops.add(4)
    me.polygons.add(1)
    colormap = ob.data.color_attributes.new(
        name='',
        type='FLOAT_COLOR',
        domain='POINT'
    )

    me.vertices[0].co = mathutils.Vector([
        metadata['floormap']['x1'] * metadata['floormap']['scale'] * -scale,
        metadata['floormap']['y1'] * metadata['floormap']['scale'] * -scale,
        0
    ])
    me.vertices[1].co = mathutils.Vector([
        metadata['floormap']['x2'] * metadata['floormap']['scale'] * -scale,
        metadata['floormap']['y1'] * metadata['floormap']['scale'] * -scale,
        0
    ])
    me.vertices[2].co = mathutils.Vector([
        metadata['floormap']['x2'] * metadata['floormap']['scale'] * -scale,
        metadata['floormap']['y2'] * metadata['floormap']['scale'] * -scale,
        0
    ])
    me.vertices[3].co = mathutils.Vector([
        metadata['floormap']['x1'] * metadata['floormap']['scale'] * -scale,
        metadata['floormap']['y2'] * metadata['floormap']['scale'] * -scale,
        0
    ])

    colormap.data[0].color = [0.5, 0.5, 0.5, 1]
    colormap.data[1].color = [0.5, 0.5, 0.5, 1]
    colormap.data[2].color = [0.5, 0.5, 0.5, 1]
    colormap.data[3].color = [0.5, 0.5, 0.5, 1]

    me.polygons[0].vertices = [0, 1, 2, 3]

    uvtex = me.uv_layers.new()
    uvtex.uv[0].vector = [0, 0]
    uvtex.uv[1].vector = [1, 0]
    uvtex.uv[2].vector = [1, 1]
    uvtex.uv[3].vector = [0, 1]

    # no edges - calculate them
    me.update(calc_edges=True)
    me.validate()

    new_objects.append(ob)
    '''

    return new_objects

def loadTrk(context, filepath, scale, trk, weather, tod):
    with open(filepath, mode='rb') as f: 
        stream = KaitaiStream(f)
        track = Srt(stream)

    if (trk == "auto"):
        trk = Path(filepath).stem.split('_')[0].lower()
        if (trk == "emrald"): trk = "emerald"

    metadata_file = (resources.files(trackmeta)) / (trk + ".json")
    with open(metadata_file, mode='r') as f:
        metadata = json.load(f)

    objlist = convertTrk(track, metadata, filepath, scale, weather, tod)
    scn = bpy.context.scene
    
    for o in scn.objects:
        o.select_set(False)
    
    for o in objlist:
        scn.collection.objects.link(o)
        if o.name.startswith("Deco"):
            # autofix weird UV issues with deco parts
            # TODO: very resource intensive. find way to avoid this
            bpy.context.view_layer.objects.active = o
            bpy.ops.object.mode_set(mode = 'EDIT')
            bpy.ops.object.mode_set(mode = 'OBJECT')

    for o in objlist:
        o.select_set(True)

    # Disable color space calculations
    bpy.context.scene.view_settings.view_transform = 'Raw'

    return {'FINISHED'}