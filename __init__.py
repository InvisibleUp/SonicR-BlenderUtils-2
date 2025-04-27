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
from PIL import Image
from bpy.props import StringProperty, EnumProperty, FloatProperty, BoolProperty
from bpy_extras.io_utils import ImportHelper
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

    usebackground: BoolProperty(
        name="Simulate background"
    )

    usedrawdistance: BoolProperty(
        name="Simulate draw distance fading"
    )

    def draw(self, context):
        layout = self.layout
        #layout.use_property_split = True
        #layout.use_property_decorate = False  # No animation
        layout.prop(self, 'scale')
        layout.prop(self, 'trk')
        layout.prop(self, 'weather')
        layout.prop(self, 'tod')
        layout.prop(self, 'usebackground')
        layout.prop(self, 'usedrawdistance')

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

''' Load a .RAW texture '''
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
    # TODO: improve speed by avoiding get/putpixel
    mask = Image.new('1', size)
    for x in range(size[0]):
        for y in range(size[1]):
            pixel = image.getpixel((x,y))
            mask.putpixel((x, y), (
                pixel != (0,255,0) and
                # some transparency regions are defined incorrectly
                pixel != (10,254,11) and
                pixel != (0,252,0)
            ))
    image.putalpha(mask)

    return image

''' Create a 1024x1024 texture combining all defined textures as one '''
# note: 1024x1024 is enough for 16 tpages. that ought to be sufficient.
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
    bpy_im.pixels = [x / 256 for x in atlas.tobytes()]
    bpy_im.pack()
    bpy_im.update()
    with bpy.context.temp_override(edit_image=bpy_im):
        bpy.ops.image.flip(use_flip_y=True)

    return bpy_im

'''Create a texture for the floormap'''
def createFloormapTexture(metadata: dict, rootPath: Path, weather: str) -> Image.Image:
    map_path = Path(rootPath, metadata['floormap']['map'])
    if weather == "snow":
        ply_path = Path(rootPath, metadata['floormap']['ply_snow'])
    else:
        ply_path = Path(rootPath, metadata['floormap']['ply'])

    # Map is a 256x256 array of tile indicies stored as bytes
    # Map needs to be cropped to the upper 128x128 tiles (the rest is blank/junk)
    # tiles are 32x32, stored in a file that's 320x384 (or 10x12 tiles)
    # i guess this means a maximum of 120 tiles? strange.

    with open(map_path, 'rb') as map_file:
        map = map_file.read()
    
    ply = loadRawTexture(ply_path)

    # final texture is 128*32 = 4096x4096
    texture = Image.new("RGBA", (4096, 4096))

    for x in range(128):
        for y in range(128):
            tile = map[y * 256 + x]
            src_x = (tile % 10) * 32
            src_y = (tile // 10) * 32
            tile_texture = ply.crop((src_x, src_y, src_x+32, src_y+32))
            texture.paste(tile_texture, (x*32, y*32))

    # convert to Blender image
    bpy_im = bpy.data.images.new("atlas", 4096, 4096)
    # Disable color space calculations
    bpy_im.colorspace_settings.name = 'Non-Color'
    # load data
    bpy_im.pixels = [x / 256 for x in texture.tobytes()]
    bpy_im.pack()
    bpy_im.update()
    with bpy.context.temp_override(edit_image=bpy_im):
        bpy.ops.image.flip(use_flip_y=True)

    return bpy_im

''' Generate a material for a given texture '''
def createMaterial(name: str, image, global_color: dict | None, weather: str, tod: str, drawdist: bool, scale: float):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    sf = scale / 0.01

    # generated by https://extensions.blender.org/add-ons/node-to-python/
    material = mat.node_tree
    material.color_tag = 'NONE'
    material.description = ""
    material.nodes.clear()

    #initialize material nodes
    #node Texture Coordinate
    texture_coordinate = material.nodes.new("ShaderNodeTexCoord")
    texture_coordinate.name = "Texture Coordinate"
    texture_coordinate.from_instancer = False

    #node Light Path
    light_path = material.nodes.new("ShaderNodeLightPath")
    light_path.name = "Light Path"

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

    #node Mix Alpha
    mix_alpha = material.nodes.new("ShaderNodeMixShader")
    mix_alpha.label = "Mix Alpha"
    mix_alpha.name = "Mix Alpha"

    #node Environment Color
    environment_color = material.nodes.new("ShaderNodeVectorMath")
    environment_color.label = "Environment Color"
    environment_color.name = "Environment Color"
    environment_color.operation = 'ADD'
    if (weather != 'none' and tod != 'none' and 'clear' in global_color):
        r = (int(global_color[weather][tod]['r'], 16) - 128) / 256
        g = (int(global_color[weather][tod]['g'], 16) - 128) / 256
        b = (int(global_color[weather][tod]['b'], 16) - 128) / 256
        environment_color.inputs[1].default_value = (r, g, b)
    elif ('r' in global_color):
        r = (int(global_color['r'], 16) - 128) / 256
        g = (int(global_color['g'], 16) - 128) / 256
        b = (int(global_color['b'], 16) - 128) / 256
        environment_color.inputs[1].default_value = (r, g, b)
    else:
        environment_color.inputs[1].default_value = (0, 0, 0)

    #node Math
    math = material.nodes.new("ShaderNodeMath")
    math.name = "Math"
    math.operation = 'ROUND'
    math.use_clamp = True

    #node Camera Data
    camera_data = material.nodes.new("ShaderNodeCameraData")
    camera_data.name = "Camera Data"

    #node Math.001
    math_001 = material.nodes.new("ShaderNodeMath")
    math_001.name = "Math.001"
    math_001.operation = 'SUBTRACT'
    math_001.use_clamp = False
    #Value_001
    math_001.inputs[1].default_value = 75.0 * sf

    #node Vector Math
    vector_math = material.nodes.new("ShaderNodeVectorMath")
    vector_math.name = "Vector Math"
    vector_math.operation = 'MULTIPLY'

    #node Combine XYZ
    combine_xyz = material.nodes.new("ShaderNodeCombineXYZ")
    combine_xyz.name = "Combine XYZ"

    #node Vector Math.001
    vector_math_001 = material.nodes.new("ShaderNodeVectorMath")
    vector_math_001.name = "Vector Math.001"
    vector_math_001.operation = 'SUBTRACT'
    #Vector
    vector_math_001.inputs[0].default_value = (1.0, 1.0, 1.0)

    #node Vector Math.002
    vector_math_002 = material.nodes.new("ShaderNodeVectorMath")
    vector_math_002.name = "Vector Math.002"
    vector_math_002.operation = 'DIVIDE'
    #Vector_001
    vector_math_002.inputs[1].default_value = (40.0 * sf, 40.0 * sf, 40.0 * sf)

    #node Vector Math.003
    vector_math_003 = material.nodes.new("ShaderNodeVectorMath")
    vector_math_003.name = "Vector Math.003"
    vector_math_003.operation = 'MINIMUM'
    #Vector_001
    vector_math_003.inputs[1].default_value = (1.0, 1.0, 1.0)

    #node Vector Math.004
    vector_math_004 = material.nodes.new("ShaderNodeVectorMath")
    vector_math_004.name = "Vector Math.004"
    vector_math_004.operation = 'MAXIMUM'
    #Vector_001
    vector_math_004.inputs[1].default_value = (0.0, 0.0, 0.0)

    #node Math.003
    math_003 = material.nodes.new("ShaderNodeMath")
    math_003.name = "Math.003"
    math_003.operation = 'SUBTRACT'
    math_003.use_clamp = False
    #Value_001
    math_003.inputs[1].default_value = 40.0 * sf

    #node Math.004
    math_004 = material.nodes.new("ShaderNodeMath")
    math_004.name = "Math.004"
    math_004.operation = 'MINIMUM'
    math_004.use_clamp = True

    #node Math.002
    math_002 = material.nodes.new("ShaderNodeMath")
    math_002.name = "Math.002"
    math_002.operation = 'SUBTRACT'
    math_002.use_clamp = True
    #Value
    math_002.inputs[0].default_value = 1.0

    #node Math.005
    math_005 = material.nodes.new("ShaderNodeMath")
    math_005.name = "Math.005"
    math_005.operation = 'DIVIDE'
    math_005.use_clamp = False
    #Value_001
    math_005.inputs[1].default_value = 20.0

    #node Vector Math.005
    vector_math_005 = material.nodes.new("ShaderNodeVectorMath")
    vector_math_005.name = "Vector Math.005"
    vector_math_005.operation = 'SNAP'
    #Vector_001
    vector_math_005.inputs[1].default_value = (0.125, 0.125, 0.125)

    #node Math.006
    math_006 = material.nodes.new("ShaderNodeMath")
    math_006.name = "Math.006"
    math_006.operation = 'SNAP'
    math_006.use_clamp = False
    #Value_001
    math_006.inputs[1].default_value = 0.25

    #node UseDrawDistance
    usedrawdistance = material.nodes.new("ShaderNodeValue")
    usedrawdistance.label = "Use Draw Distance"
    usedrawdistance.name = "UseDrawDistance"
    usedrawdistance.outputs[0].default_value = 1.0 if drawdist else 0.0

    #node Math.007
    math_007 = material.nodes.new("ShaderNodeMath")
    math_007.name = "Math.007"
    math_007.operation = 'MULTIPLY'
    math_007.use_clamp = False


    #Set locations
    texture_coordinate.location = (-752.1420288085938, 172.89166259765625)
    light_path.location = (-255.24154663085938, 58.26454544067383)
    material_output.location = (852.327880859375, 230.1283416748047)
    color_attribute.location = (-1184.246826171875, 400.07073974609375)
    add_vertex_color.location = (-252.72947692871094, 380.2495422363281)
    adjust_vertex_color.location = (-978.760498046875, 452.8673095703125)
    image_texture.location = (-555.6151123046875, 191.15330505371094)
    transparent_bsdf.location = (-37.10700988769531, 387.06463623046875)
    emission.location = (-38.904380798339844, 288.57635498046875)
    mix_alpha.location = (616.8135986328125, 206.23117065429688)
    environment_color.location = (-751.8001708984375, 448.4853210449219)
    math.location = (-36.93527603149414, 163.29348754882812)
    camera_data.location = (-2404.267578125, 552.5215454101562)
    math_001.location = (-2025.0885009765625, 563.6470336914062)
    vector_math.location = (-542.4853515625, 655.0713500976562)
    combine_xyz.location = (-1808.0262451171875, 563.6287231445312)
    vector_math_001.location = (-984.9356079101562, 723.4531860351562)
    vector_math_002.location = (-1598.12646484375, 760.7192993164062)
    vector_math_003.location = (-1398.326904296875, 798.4099731445312)
    vector_math_004.location = (-1213.947021484375, 767.1242065429688)
    math_003.location = (-1599.229248046875, 989.9688110351562)
    math_004.location = (318.064208984375, 564.293701171875)
    math_002.location = (-1221.552490234375, 996.1053466796875)
    math_005.location = (-1403.4525146484375, 999.1436767578125)
    vector_math_005.location = (-768.5155029296875, 755.4838256835938)
    math_006.location = (-1040.7615966796875, 1004.9134521484375)
    usedrawdistance.location = (-2402.180419921875, 668.9149780273438)
    math_007.location = (-2215.785888671875, 625.6062622070312)

    #Set dimensions
    texture_coordinate.width, texture_coordinate.height = 140.0, 100.0
    light_path.width, light_path.height = 140.0, 100.0
    material_output.width, material_output.height = 140.0, 100.0
    color_attribute.width, color_attribute.height = 140.0, 100.0
    add_vertex_color.width, add_vertex_color.height = 140.0, 100.0
    adjust_vertex_color.width, adjust_vertex_color.height = 140.0, 100.0
    image_texture.width, image_texture.height = 240.0, 100.0
    transparent_bsdf.width, transparent_bsdf.height = 140.0, 100.0
    emission.width, emission.height = 140.0, 100.0
    mix_alpha.width, mix_alpha.height = 140.0, 100.0
    environment_color.width, environment_color.height = 140.0, 100.0
    math.width, math.height = 140.0, 100.0
    camera_data.width, camera_data.height = 140.0, 100.0
    math_001.width, math_001.height = 140.0, 100.0
    vector_math.width, vector_math.height = 140.0, 100.0
    combine_xyz.width, combine_xyz.height = 140.0, 100.0
    vector_math_001.width, vector_math_001.height = 140.0, 100.0
    vector_math_002.width, vector_math_002.height = 140.0, 100.0
    vector_math_003.width, vector_math_003.height = 140.0, 100.0
    vector_math_004.width, vector_math_004.height = 140.0, 100.0
    math_003.width, math_003.height = 140.0, 100.0
    math_004.width, math_004.height = 140.0, 100.0
    math_002.width, math_002.height = 140.0, 100.0
    math_005.width, math_005.height = 140.0, 100.0
    vector_math_005.width, vector_math_005.height = 140.0, 100.0
    math_006.width, math_006.height = 140.0, 100.0
    usedrawdistance.width, usedrawdistance.height = 140.0, 100.0
    math_007.width, math_007.height = 140.0, 100.0

    #initialize material links
    #texture_coordinate.UV -> image_texture.Vector
    material.links.new(texture_coordinate.outputs[2], image_texture.inputs[0])
    #image_texture.Color -> add_vertex_color.Vector
    material.links.new(image_texture.outputs[0], add_vertex_color.inputs[1])
    #color_attribute.Color -> adjust_vertex_color.Vector
    material.links.new(color_attribute.outputs[0], adjust_vertex_color.inputs[0])
    #emission.Emission -> mix_alpha.Shader
    material.links.new(emission.outputs[0], mix_alpha.inputs[2])
    #adjust_vertex_color.Vector -> environment_color.Vector
    material.links.new(adjust_vertex_color.outputs[0], environment_color.inputs[0])
    #transparent_bsdf.BSDF -> mix_alpha.Shader
    material.links.new(transparent_bsdf.outputs[0], mix_alpha.inputs[1])
    #mix_alpha.Shader -> material_output.Surface
    material.links.new(mix_alpha.outputs[0], material_output.inputs[0])
    #light_path.Is Camera Ray -> emission.Strength
    material.links.new(light_path.outputs[0], emission.inputs[1])
    #add_vertex_color.Vector -> emission.Color
    material.links.new(add_vertex_color.outputs[0], emission.inputs[0])
    #image_texture.Alpha -> math.Value
    material.links.new(image_texture.outputs[1], math.inputs[0])
    #environment_color.Vector -> vector_math.Vector
    material.links.new(environment_color.outputs[0], vector_math.inputs[1])
    #math_001.Value -> combine_xyz.X
    material.links.new(math_001.outputs[0], combine_xyz.inputs[0])
    #math_001.Value -> combine_xyz.Y
    material.links.new(math_001.outputs[0], combine_xyz.inputs[1])
    #math_001.Value -> combine_xyz.Z
    material.links.new(math_001.outputs[0], combine_xyz.inputs[2])
    #combine_xyz.Vector -> vector_math_002.Vector
    material.links.new(combine_xyz.outputs[0], vector_math_002.inputs[0])
    #vector_math_002.Vector -> vector_math_003.Vector
    material.links.new(vector_math_002.outputs[0], vector_math_003.inputs[0])
    #vector_math_003.Vector -> vector_math_004.Vector
    material.links.new(vector_math_003.outputs[0], vector_math_004.inputs[0])
    #vector_math_004.Vector -> vector_math_001.Vector
    material.links.new(vector_math_004.outputs[0], vector_math_001.inputs[1])
    #math.Value -> math_004.Value
    material.links.new(math.outputs[0], math_004.inputs[1])
    #math_004.Value -> mix_alpha.Fac
    material.links.new(math_004.outputs[0], mix_alpha.inputs[0])
    #math_003.Value -> math_005.Value
    material.links.new(math_003.outputs[0], math_005.inputs[0])
    #math_005.Value -> math_002.Value
    material.links.new(math_005.outputs[0], math_002.inputs[1])
    #vector_math.Vector -> add_vertex_color.Vector
    material.links.new(vector_math.outputs[0], add_vertex_color.inputs[0])
    #vector_math_001.Vector -> vector_math_005.Vector
    material.links.new(vector_math_001.outputs[0], vector_math_005.inputs[0])
    #vector_math_005.Vector -> vector_math.Vector
    material.links.new(vector_math_005.outputs[0], vector_math.inputs[0])
    #math_006.Value -> math_004.Value
    material.links.new(math_006.outputs[0], math_004.inputs[0])
    #math_002.Value -> math_006.Value
    material.links.new(math_002.outputs[0], math_006.inputs[0])
    #math_001.Value -> math_003.Value
    material.links.new(math_001.outputs[0], math_003.inputs[0])
    #usedrawdistance.Value -> math_007.Value
    material.links.new(usedrawdistance.outputs[0], math_007.inputs[0])
    #camera_data.View Z Depth -> math_007.Value
    material.links.new(camera_data.outputs[1], math_007.inputs[1])
    #math_007.Value -> math_001.Value
    material.links.new(math_007.outputs[0], math_001.inputs[0])
    return mat

''' Sets the world background '''
def setWorldBackground(metadata: dict, rootPath: Path, weather: str, tod: str):
    if not 'bg' in metadata: return

    # Retrieve metadata/textures
    has_water = False
    if isinstance(metadata['bg'], str):
        bg_path = metadata['bg']
    else:
        if weather not in metadata['bg']: return
        if tod not in metadata['bg'][weather]: return
        bg_path = metadata['bg'][weather][tod]
        if 'has_water' in metadata['bg']:
            has_water = metadata['bg']['has_water']
    bg_path = Path(rootPath).joinpath(bg_path)
    bg_raw = loadRawTexture(bg_path)
    # convert to Blender image
    bg_image = bpy.data.images.new("atlas", 1664, 128)
    # Disable color space calculations
    bg_image.colorspace_settings.name = 'Non-Color'
    # load data
    bg_image.pixels = [x / 256 for x in bg_raw.tobytes()]
    bg_image.pack()
    bg_image.update()
    with bpy.context.temp_override(edit_image=bg_image):
        bpy.ops.image.flip(use_flip_y=True)

    if (weather != 'none' and tod != 'none' and 'clear' in metadata['global_color']):
        r = (int(metadata['global_color'][weather][tod]['r'], 16) - 128) / 256
        g = (int(metadata['global_color'][weather][tod]['g'], 16) - 128) / 256
        b = (int(metadata['global_color'][weather][tod]['b'], 16) - 128) / 256
    else:
        r = 0
        g = 0
        b = 0

    #start with a clean node tree
    skybox = bpy.data.worlds["World"].node_tree
    for node in skybox.nodes:
        skybox.nodes.remove(node)
    skybox.color_tag = 'NONE'
    skybox.description = ""

    #initialize skybox nodes
    #node World Output
    world_output = skybox.nodes.new("ShaderNodeOutputWorld")
    world_output.name = "World Output"
    world_output.is_active_output = True
    world_output.target = 'ALL'

    #node Background
    background = skybox.nodes.new("ShaderNodeBackground")
    background.name = "Background"
    #Strength
    background.inputs[1].default_value = 1.0

    #node Wave Texture
    wave_texture = skybox.nodes.new("ShaderNodeTexWave")
    wave_texture.name = "Wave Texture"
    wave_texture.bands_direction = 'Z'
    wave_texture.rings_direction = 'SPHERICAL'
    wave_texture.wave_profile = 'SIN'
    wave_texture.wave_type = 'BANDS'
    #Scale
    wave_texture.inputs[1].default_value = 10.0
    #Distortion
    wave_texture.inputs[2].default_value = 0.0
    #Detail
    wave_texture.inputs[3].default_value = 2.0
    #Detail Scale
    wave_texture.inputs[4].default_value = 1.0
    #Detail Roughness
    wave_texture.inputs[5].default_value = 0.5
    #Phase Offset
    wave_fcurve = wave_texture.inputs[6].driver_add("default_value")
    wave_driver = wave_fcurve.driver
    wave_driver.type = "SCRIPTED"
    wave_driver.expression = "-frame/5"

    #node Mix.002
    mix_002 = skybox.nodes.new("ShaderNodeMix")
    mix_002.name = "Mix.002"
    mix_002.blend_type = 'MIX'
    mix_002.clamp_factor = False
    mix_002.clamp_result = False
    mix_002.data_type = 'RGBA'
    mix_002.factor_mode = 'UNIFORM'
    #A_Color
    mix_002.inputs[6].default_value = (0.19 + r, 0.66 + g, 0.82 + b, 1.0)
    #B_Color
    mix_002.inputs[7].default_value = (0.0 + r, 1.0 + g, 1.0 + b, 1.0)

    #node Geometry
    geometry = skybox.nodes.new("ShaderNodeNewGeometry")
    geometry.name = "Geometry"

    #node Image Texture
    image_texture = skybox.nodes.new("ShaderNodeTexImage")
    image_texture.name = "Image Texture"
    image_texture.extension = 'EXTEND'
    image_texture.image_user.frame_current = 0
    image_texture.image_user.frame_duration = 100
    image_texture.image_user.frame_offset = 0
    image_texture.image_user.frame_start = 1
    image_texture.image_user.tile = 0
    image_texture.image_user.use_auto_refresh = False
    image_texture.image_user.use_cyclic = False
    image_texture.interpolation = 'Closest'
    image_texture.projection = 'FLAT'
    image_texture.projection_blend = 0.0
    image_texture.image = bg_image

    #node Separate XYZ
    separate_xyz = skybox.nodes.new("ShaderNodeSeparateXYZ")
    separate_xyz.name = "Separate XYZ"

    #node Combine XYZ
    combine_xyz = skybox.nodes.new("ShaderNodeCombineXYZ")
    combine_xyz.name = "Combine XYZ"
    #Z
    combine_xyz.inputs[2].default_value = 0.0

    #node Math
    math = skybox.nodes.new("ShaderNodeMath")
    math.name = "Math"
    math.operation = 'MULTIPLY'
    math.use_clamp = True
    #Value_001
    math.inputs[1].default_value = 4.0

    #node Math.001
    math_001 = skybox.nodes.new("ShaderNodeMath")
    math_001.name = "Math.001"
    math_001.operation = 'LESS_THAN'
    math_001.use_clamp = False
    #Value_001
    math_001.inputs[1].default_value = 0.0

    #node Mix
    mix = skybox.nodes.new("ShaderNodeMix")
    mix.name = "Mix"
    mix.blend_type = 'MIX'
    mix.clamp_factor = False
    mix.clamp_result = False
    mix.data_type = 'FLOAT'
    mix.factor_mode = 'UNIFORM'

    #node Math.002
    math_002 = skybox.nodes.new("ShaderNodeMath")
    math_002.name = "Math.002"
    math_002.operation = 'MULTIPLY'
    math_002.use_clamp = True
    #Value_001
    math_002.inputs[1].default_value = -6.0

    #node Math.004
    math_004 = skybox.nodes.new("ShaderNodeMath")
    math_004.name = "Math.004"
    math_004.operation = 'DIVIDE'
    math_004.use_clamp = False
    #Value_001
    math_004.inputs[1].default_value = -3.141590118408203

    #node Math.005
    math_005 = skybox.nodes.new("ShaderNodeMath")
    math_005.name = "Math.005"
    math_005.operation = 'ARCTAN2'
    math_005.use_clamp = False

    #node Math.006
    math_006 = skybox.nodes.new("ShaderNodeMath")
    math_006.name = "Math.006"
    math_006.operation = 'FRACT'
    math_006.use_clamp = False

    #node Mix.001
    mix_001 = skybox.nodes.new("ShaderNodeMix")
    mix_001.name = "Mix.001"
    mix_001.blend_type = 'ADD'
    mix_001.clamp_factor = True
    mix_001.clamp_result = False
    mix_001.data_type = 'RGBA'
    mix_001.factor_mode = 'UNIFORM'

    #node Vector Math
    vector_math = skybox.nodes.new("ShaderNodeVectorMath")
    vector_math.name = "Vector Math"
    vector_math.operation = 'DIVIDE'
    #Vector_001
    vector_math.inputs[1].default_value = (3.0, 3.0, 3.0)

    #node Math.003
    math_003 = skybox.nodes.new("ShaderNodeMath")
    math_003.name = "Math.003"
    math_003.operation = 'ADD'
    math_003.use_clamp = False

    #node Math.007
    math_007 = skybox.nodes.new("ShaderNodeMath")
    math_007.name = "Math.007"
    math_007.operation = 'DIVIDE'
    math_007.use_clamp = False
    #Value_001
    math_007.inputs[1].default_value = 16.0

    #node Combine XYZ.001
    combine_xyz_001 = skybox.nodes.new("ShaderNodeCombineXYZ")
    combine_xyz_001.name = "Combine XYZ.001"
    #X
    combine_xyz_001.inputs[0].default_value = 0.0
    #Y
    combine_xyz_001.inputs[1].default_value = 0.0

    #node Math.013
    math_013 = skybox.nodes.new("ShaderNodeMath")
    math_013.name = "Math.013"
    math_013.operation = 'POWER'
    math_013.use_clamp = True
    #Value_001
    math_013.inputs[1].default_value = 0.10000000149011612

    #node Math.014
    math_014 = skybox.nodes.new("ShaderNodeMath")
    math_014.name = "Math.014"
    math_014.operation = 'MULTIPLY'
    math_014.use_clamp = False
    #Value_001
    math_014.inputs[1].default_value = -1.0

    #node Map Range
    map_range = skybox.nodes.new("ShaderNodeMapRange")
    map_range.name = "Map Range"
    map_range.clamp = True
    map_range.data_type = 'FLOAT'
    map_range.interpolation_type = 'LINEAR'
    #From Min
    map_range.inputs[1].default_value = 0.25
    #From Max
    map_range.inputs[2].default_value = 0.75
    #To Min
    map_range.inputs[3].default_value = 0.0
    #To Max
    map_range.inputs[4].default_value = 1.0

    #node Math.015
    math_015 = skybox.nodes.new("ShaderNodeMath")
    math_015.name = "Math.015"
    math_015.operation = 'ADD'
    math_015.use_clamp = False
    #Value_001
    math_015.inputs[1].default_value = -0.5

    #node Water Enabled
    water_enabled = skybox.nodes.new("ShaderNodeValue")
    water_enabled.label = "Water Enabled"
    water_enabled.name = "Water Enabled"
    water_enabled.outputs[0].default_value = 1.0 if has_water else 0.0

    #node Math.008
    math_008 = skybox.nodes.new("ShaderNodeMath")
    math_008.name = "Math.008"
    math_008.operation = 'MULTIPLY'
    math_008.use_clamp = False

    #node Math.009
    math_009 = skybox.nodes.new("ShaderNodeMath")
    math_009.name = "Math.009"
    math_009.operation = 'MULTIPLY'
    math_009.use_clamp = False


    #Set locations
    world_output.location = (-757.238525390625, 778.646484375)
    background.location = (-976.409423828125, 797.6539306640625)
    wave_texture.location = (-3554.89404296875, 1184.552734375)
    mix_002.location = (-1631.6536865234375, 895.7874755859375)
    geometry.location = (-4599.33154296875, 676.36767578125)
    image_texture.location = (-1496.288330078125, 546.562255859375)
    separate_xyz.location = (-4354.81640625, 723.9926147460938)
    combine_xyz.location = (-1739.6473388671875, 531.3412475585938)
    math.location = (-2519.0595703125, 383.3988342285156)
    math_001.location = (-2518.927490234375, 555.941162109375)
    mix.location = (-1986.791748046875, 483.0517883300781)
    math_002.location = (-2758.73828125, 15.614013671875)
    math_004.location = (-2505.093505859375, 845.13818359375)
    math_005.location = (-2693.676513671875, 837.2177734375)
    math_006.location = (-2325.196044921875, 809.7803955078125)
    mix_001.location = (-1193.0732421875, 767.93603515625)
    vector_math.location = (-1416.1317138671875, 908.6997680664062)
    math_003.location = (-2212.44677734375, 227.21624755859375)
    math_007.location = (-2756.41455078125, 203.84359741210938)
    combine_xyz_001.location = (-3765.7373046875, 1060.7265625)
    math_013.location = (-3942.17041015625, 983.3365478515625)
    math_014.location = (-4128.26025390625, 888.9439086914062)
    map_range.location = (-1884.691162109375, 1116.2166748046875)
    math_015.location = (-2966.29638671875, 212.31423950195312)
    water_enabled.location = (-2764.30712890625, 424.85443115234375)
    math_008.location = (-2514.138427734375, 207.23936462402344)
    math_009.location = (-2190.78759765625, 637.00537109375)

    #Set dimensions
    world_output.width, world_output.height = 140.0, 100.0
    background.width, background.height = 140.0, 100.0
    wave_texture.width, wave_texture.height = 150.0, 100.0
    mix_002.width, mix_002.height = 140.0, 100.0
    geometry.width, geometry.height = 140.0, 100.0
    image_texture.width, image_texture.height = 240.0, 100.0
    separate_xyz.width, separate_xyz.height = 140.0, 100.0
    combine_xyz.width, combine_xyz.height = 140.0, 100.0
    math.width, math.height = 140.0, 100.0
    math_001.width, math_001.height = 140.0, 100.0
    mix.width, mix.height = 140.0, 100.0
    math_002.width, math_002.height = 140.0, 100.0
    math_004.width, math_004.height = 140.0, 100.0
    math_005.width, math_005.height = 140.0, 100.0
    math_006.width, math_006.height = 140.0, 100.0
    mix_001.width, mix_001.height = 140.0, 100.0
    vector_math.width, vector_math.height = 140.0, 100.0
    math_003.width, math_003.height = 140.0, 100.0
    math_007.width, math_007.height = 140.0, 100.0
    combine_xyz_001.width, combine_xyz_001.height = 140.0, 100.0
    math_013.width, math_013.height = 140.0, 100.0
    math_014.width, math_014.height = 140.0, 100.0
    map_range.width, map_range.height = 140.0, 100.0
    math_015.width, math_015.height = 140.0, 100.0
    water_enabled.width, water_enabled.height = 140.0, 100.0
    math_008.width, math_008.height = 140.0, 100.0
    math_009.width, math_009.height = 140.0, 100.0

    #initialize skybox links
    #background.Background -> world_output.Surface
    skybox.links.new(background.outputs[0], world_output.inputs[0])
    #combine_xyz.Vector -> image_texture.Vector
    skybox.links.new(combine_xyz.outputs[0], image_texture.inputs[0])
    #geometry.Position -> separate_xyz.Vector
    skybox.links.new(geometry.outputs[0], separate_xyz.inputs[0])
    #separate_xyz.Z -> math.Value
    skybox.links.new(separate_xyz.outputs[2], math.inputs[0])
    #separate_xyz.Z -> math_001.Value
    skybox.links.new(separate_xyz.outputs[2], math_001.inputs[0])
    #math_001.Value -> mix.Factor
    skybox.links.new(math_001.outputs[0], mix.inputs[0])
    #math.Value -> mix.A
    skybox.links.new(math.outputs[0], mix.inputs[2])
    #mix.Result -> combine_xyz.Y
    skybox.links.new(mix.outputs[0], combine_xyz.inputs[1])
    #math_005.Value -> math_004.Value
    skybox.links.new(math_005.outputs[0], math_004.inputs[0])
    #separate_xyz.X -> math_005.Value
    skybox.links.new(separate_xyz.outputs[0], math_005.inputs[0])
    #separate_xyz.Y -> math_005.Value
    skybox.links.new(separate_xyz.outputs[1], math_005.inputs[1])
    #math_004.Value -> math_006.Value
    skybox.links.new(math_004.outputs[0], math_006.inputs[0])
    #mix_002.Result -> vector_math.Vector
    skybox.links.new(mix_002.outputs[2], vector_math.inputs[0])
    #math_015.Value -> math_007.Value
    skybox.links.new(math_015.outputs[0], math_007.inputs[0])
    #combine_xyz_001.Vector -> wave_texture.Vector
    skybox.links.new(combine_xyz_001.outputs[0], wave_texture.inputs[0])
    #math_013.Value -> combine_xyz_001.Z
    skybox.links.new(math_013.outputs[0], combine_xyz_001.inputs[2])
    #separate_xyz.Z -> math_014.Value
    skybox.links.new(separate_xyz.outputs[2], math_014.inputs[0])
    #math_014.Value -> math_013.Value
    skybox.links.new(math_014.outputs[0], math_013.inputs[0])
    #vector_math.Vector -> mix_001.B
    skybox.links.new(vector_math.outputs[0], mix_001.inputs[7])
    #wave_texture.Fac -> map_range.Value
    skybox.links.new(wave_texture.outputs[1], map_range.inputs[0])
    #map_range.Result -> mix_002.Factor
    skybox.links.new(map_range.outputs[0], mix_002.inputs[0])
    #wave_texture.Fac -> math_015.Value
    skybox.links.new(wave_texture.outputs[1], math_015.inputs[0])
    #mix_001.Result -> background.Color
    skybox.links.new(mix_001.outputs[2], background.inputs[0])
    #image_texture.Color -> mix_001.A
    skybox.links.new(image_texture.outputs[0], mix_001.inputs[6])
    #separate_xyz.Z -> math_002.Value
    skybox.links.new(separate_xyz.outputs[2], math_002.inputs[0])
    #math_006.Value -> combine_xyz.X
    skybox.links.new(math_006.outputs[0], combine_xyz.inputs[0])
    #math_002.Value -> math_003.Value
    skybox.links.new(math_002.outputs[0], math_003.inputs[1])
    #math_003.Value -> mix.B
    skybox.links.new(math_003.outputs[0], mix.inputs[3])
    #math_008.Value -> math_003.Value
    skybox.links.new(math_008.outputs[0], math_003.inputs[0])
    #math_001.Value -> math_009.Value
    skybox.links.new(math_001.outputs[0], math_009.inputs[0])
    #math_009.Value -> mix_001.Factor
    skybox.links.new(math_009.outputs[0], mix_001.inputs[0])
    #water_enabled.Value -> math_009.Value
    skybox.links.new(water_enabled.outputs[0], math_009.inputs[1])
    #water_enabled.Value -> math_008.Value
    skybox.links.new(water_enabled.outputs[0], math_008.inputs[0])
    #math_007.Value -> math_008.Value
    skybox.links.new(math_007.outputs[0], math_008.inputs[1])

# Convert a raw tpage/texture coordinate to a position on the texture atlas
def getTextureCoords(tpage: int, x: int, y: int) -> (float, float):
    # convert to float
    # the atlas is a 4x4 array of tpages, so compensate
    (x2, y2) = (x / 1024, y / 1024)

    # for some reason, I'm getting tpages much larger than they should be
    # possible parsing issue?
    tpage = tpage % 2**16

    # tpage offset
    x2 += (tpage % 4) / 4
    y2 += (tpage // 4) / 4

    # debug asserts
    assert y2 <= 1, (tpage, y, y2)
    assert y2 >= 0, (tpage, y, y2)

    return (x2, (-y2 + 1))

def convertTrk(
        srt: Srt,
        metadata: dict,
        filepath: str,
        scale: float,
        weather: str,
        tod: str,
        usedrawdistance: bool,
        usebackground: bool
    ):
    # TODO: handle case-insensitive file systems
    trkPath = str(Path(metadata['file_trk'].lower()))
    rootPath = str(Path(filepath.lower())).removesuffix(trkPath)

    # collections
    grpGeom = bpy.data.collections.new("Track Geometry")
    grpObj  = bpy.data.collections.new("Track Objects")
    grpMeta = bpy.data.collections.new("Track Metadata")

    # set world background
    if usebackground:
        setWorldBackground(metadata, rootPath, weather, tod)

    # texture atlas
    atlas = createTextureAtlas(metadata, rootPath, weather)
    mainMaterial = createMaterial('main', atlas, metadata['global_color'], weather, tod, usedrawdistance, scale)
    
    for i, trkPart in enumerate(srt.trkparts):

        # Track mesh
        me = bpy.data.meshes.new(f"Trk.{i}") 
        ob = bpy.data.objects.new(f"Trk.{i}", me)

        # add all materials to mesh
        me.materials.append(mainMaterial)

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
        
        grpGeom.objects.link(ob)

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

            grpObj.objects.link(ob)
        
    # Decoration parts
    for i, decoPart in enumerate(srt.decoparts):
        # create a new mesh
        me = bpy.data.meshes.new(f"Deco.{i}") 
        ob = bpy.data.objects.new(f"Deco.{i}", me)
        
        # add all materials to mesh
        me.materials.append(mainMaterial)

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

        grpGeom.objects.link(ob)

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
    grpMeta.objects.link(ob)

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
    grpMeta.objects.link(ob)
    '''

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
    grpMeta.objects.link(ob)
    '''

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
    grpMeta.objects.link(ob)

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
    grpMeta.objects.link(ob)

    # replay camera points
    if (srt.num_replaypos < 0xFFFF):
        me = bpy.data.meshes.new("ReplayCamPoints") 
        ob = bpy.data.objects.new("ReplayCamPoints", me)
        me.vertices.add(srt.num_replaypos)
        for j, subobj in enumerate(srt.replaypos):
            me.vertices[j].co = mathutils.Vector([
                subobj.x * -scale,
                subobj.z * scale,
                subobj.y * scale
            ])
        grpMeta.objects.link(ob)

    # excluding Sec9 for now

    # floormap
    if ('floormap' in metadata):
        floor_image = createFloormapTexture(metadata, rootPath, weather)
        floor_material = createMaterial("FloorMap", floor_image, metadata['global_color'], weather, tod, False, scale)
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

        grpGeom.objects.link(ob)

    return [grpGeom, grpObj, grpMeta]

def loadTrk(context, filepath, scale, trk, weather, tod, usedrawdistance, usebackground):
    with open(filepath, mode='rb') as f: 
        stream = KaitaiStream(f)
        track = Srt(stream)

    if (trk == "auto"):
        trk = Path(filepath).stem.split('_')[0].lower()
        if (trk == "emrald"): trk = "emerald"
        if (trk == "factry"): trk = "factory"

    metadata_file = (resources.files(trackmeta)) / (trk + ".json")
    with open(metadata_file, mode='r') as f:
        metadata = json.load(f)
    if 'global_color' not in metadata:
        metadata['global_color'] = {}

    grplist = convertTrk(track, metadata, filepath, scale, weather, tod, usedrawdistance, usebackground)
    scn = bpy.context.scene
    
    for o in scn.objects:
        o.select_set(False)
    
    for o in grplist:
        scn.collection.children.link(o)

    # Disable color space calculations
    bpy.context.scene.view_settings.view_transform = 'Raw'

    # Set scene framerate if using animated background
    if usebackground:
        bpy.context.scene.render.fps = 30

    return {'FINISHED'}
