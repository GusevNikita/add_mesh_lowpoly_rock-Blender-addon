# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

# <pep8 compliant>

bl_info = {
    "name": "LowPoly Rock",
    "author": "Hidesato Ikeya",
    "version": (0, 2, 0),
    "blender": (4, 0, 0),
    "location": "VIEW3D > ADD > Mesh",
    "description": "LowPoly Rock",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Add Mesh"}

import bpy
import bmesh
from mathutils import Matrix
from math import radians
from random import seed, uniform

ROCK_NAME = "LowPolyRock"
ORIGIN_NAME = ROCK_NAME + "DisplaceOrigin"
TEXTURE_NAME = ROCK_NAME + "Texture"
ANGLE_MAX = radians(90)


def get_basemesh(context, subdiv=5, radius=1.0, ratio=(1., 1., 1.)):
    me = bpy.data.meshes.new('tempmeshname')
    bm = bmesh.new()
    mat = Matrix()
    mat[0][0], mat[1][1], mat[2][2] = ratio
    bmesh.ops.create_icosphere(
        bm, subdivisions=subdiv, radius=radius, matrix=mat)
    bm.to_mesh(me)
    bm.free()  # Освобождаем ресурсы
    return me

def get_texture(name, size=1.0, brightness=.8, contrast=.8,
                weights=(1.0, .3, .0)):
    tex = bpy.data.textures.new(name, 'VORONOI')
    tex.noise_scale = size
    tex.intensity = brightness
    tex.contrast = contrast
    tex.weight_1, tex.weight_2, tex.weight_3 = weights
    tex.use_color_ramp = True

    ramp = tex.color_ramp
    ramp.interpolation = 'B_SPLINE'
    ramp.elements[0].color = (.0, .0, .0, 1.0)
    ramp.elements[0].position = .5
    return tex

def create_rock(context, subdiv, radius, size_ratio,
                noise_center, noise_size, noise_brightness,
                sharpness, displace_midlevel, displace_strength,
                voronoi_weights, simplicity, collapse_ratio):
    me = get_basemesh(context, subdiv, radius, size_ratio)
    rock = bpy.data.objects.new(ROCK_NAME, me)
    context.collection.objects.link(rock)
    bpy.context.view_layer.objects.active = rock

    # Displacement
    noise_origin = bpy.data.objects.new(ORIGIN_NAME, None)
    noise_origin.location = noise_center
    noise_origin.location *= radius
    context.collection.objects.link(noise_origin)

    disp = rock.modifiers.new(name='Displace', type='DISPLACE')
    disp.direction = 'NORMAL'
    disp.mid_level = displace_midlevel
    disp.strength = radius * displace_strength
    disp.texture_coords = 'OBJECT'
    disp.texture_coords_object = noise_origin
    disp.texture = get_texture(
        TEXTURE_NAME, size=radius * noise_size, brightness=noise_brightness,
        contrast=sharpness, weights=voronoi_weights)

    # Collapse
    collapse = rock.modifiers.new(name='Decimate', type='DECIMATE')
    collapse.ratio = collapse_ratio

    # Planer (Диссольв грани)
    planer = rock.modifiers.new(name='Planar', type='DECIMATE')
    planer.decimate_type = 'DISSOLVE'
    planer.angle_limit = simplicity * ANGLE_MAX
    planer.use_dissolve_boundaries = True

    return rock, noise_origin


class LowPolyRock(bpy.types.Operator):
    """LowPoly Rock"""
    bl_idname = "mesh.lowpoly_rock_add"
    bl_label = "LowPoly Rock"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    num_rock: bpy.props.IntProperty(
        name="Number", min=1, max=9, default=1,
        description="Number of rocks")
    size: bpy.props.FloatProperty(
        name="Size", min=.0, default=1.0, precision=3, step=0.01)
    size_ratio: bpy.props.FloatVectorProperty(
        name="Size Ratio", size=3, min=.0, default=(1., 1., 1.),
        subtype='XYZ', step=0.1, precision=2, description="Size ratio")
    displace_midlevel: bpy.props.FloatProperty(
        name="Midlevel", min=.0, max=1.0, default=.5, precision=3, step=0.1)
    noise_center: bpy.props.FloatVectorProperty(
        name="Noise Center", size=3, step=0.1, subtype='XYZ',
        description="Displacement noise texture origin")
    simplicity: bpy.props.FloatProperty(
        name="Simplicity", min=.0, max=1.0, default=0.25,
        precision=2, step=0.1, description="Reduce polygons")
    sharpness: bpy.props.FloatProperty(
        name="Sharpness", min=.0, max=2.0, default=.8, precision=3, step=0.1)
    edge_split: bpy.props.BoolProperty(
        name="Edge Split", default=True,
        description="Shade smooth and add edge split modifier")

    random_seed: bpy.props.IntProperty(
        name="Random Seed", min=-1, default=0,
        description="Random seed (set -1 to use system clock)")
    size_min: bpy.props.FloatProperty(
        name="Size Min", min=-1.0, max=.0, default=-.3, precision=3, step=0.01)
    size_max: bpy.props.FloatProperty(
        name="Size Max", min=.0, default=.3, precision=3, step=0.01)
    size_ratio_min: bpy.props.FloatVectorProperty(
        name="Ratio Min", size=3, min=-1.0, max=.0, default=(-.2, -.2, -.2),
        precision=3, step=0.01)
    size_ratio_max: bpy.props.FloatVectorProperty(
        name="Ratio Max", size=3, min=.0, default=(.2, .2, .2),
        precision=3, step=0.01)

    keep_modifiers: bpy.props.BoolProperty(
        name="Keep Modifiers", default=False,
        description="Keep modifiers")
    advanced_menu: bpy.props.BoolProperty(
        name="Advanced Menu", default=False,
        description="Display advanced menu")
    voronoi_weights: bpy.props.FloatVectorProperty(
        name="Voronoi Weights", min=-1.0, max=1.0, size=3,
        default=(1.,.3,.0), step=0.1, description="Voronoi Weights")
    displace_strength: bpy.props.FloatProperty(
        name="Strength", min=.0, default=1.0, precision=3, step=0.1)
    noise_size: bpy.props.FloatProperty(
        name="Noise Size", min=.0, default=1.0, precision=3, step=0.1)
    noise_brightness: bpy.props.FloatProperty(
        name="Noise Brightness", min=.0, max=1.5, default=.8, precision=3, step=0.1)
    subdiv: bpy.props.IntProperty(
        name="Subdivision", min=1, max=7, default=5,
        description="Icosphere subdivision")
    collapse_ratio: bpy.props.FloatProperty(
        name="Collapse Ratio", min=.0, max=1.0, default=.06,
        precision=3, step=0.01)

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def draw(self, context):
        layout = self.layout
        basic = layout.box()
        basic.label(text="Basic Settings:")
        basic.prop(self, 'num_rock')
        basic.prop(self, 'size')
        basic.prop(self, 'size_ratio')
        basic.prop(self, 'random_seed')
        basic.prop(self, 'edge_split')

        advanced = layout.box()
        advanced.prop(self, 'advanced_menu')
        if self.advanced_menu:
            advanced.label(text="Advanced Settings:")
            advanced.prop(self, 'subdiv')
            advanced.prop(self, 'displace_midlevel')
            advanced.prop(self, 'displace_strength')
            advanced.prop(self, 'noise_center')
            advanced.prop(self, 'noise_size')
            advanced.prop(self, 'noise_brightness')
            advanced.prop(self, 'voronoi_weights')
            advanced.prop(self, 'sharpness')
            advanced.prop(self, 'simplicity')
            advanced.prop(self, 'collapse_ratio')

    def execute(self, context):
        seed(self.random_seed)

        for _ in range(self.num_rock):
            size = self.size * uniform(1. + self.size_min, 1. + self.size_max)
            ratio = (uniform(self.size_ratio[0] + self.size_ratio_min[0],
                             self.size_ratio[0] + self.size_ratio_max[0]),
                     uniform(self.size_ratio[1] + self.size_ratio_min[1],
                             self.size_ratio[1] + self.size_ratio_max[1]),
                     uniform(self.size_ratio[2] + self.size_ratio_min[2],
                             self.size_ratio[2] + self.size_ratio_max[2]))

            create_rock(context, subdiv=self.subdiv, radius=size,
                        size_ratio=ratio, noise_center=self.noise_center,
                        noise_size=self.noise_size,
                        noise_brightness=self.noise_brightness,
                        sharpness=self.sharpness,
                        displace_midlevel=self.displace_midlevel,
                        displace_strength=self.displace_strength,
                        voronoi_weights=self.voronoi_weights,
                        simplicity=self.simplicity,
                        collapse_ratio=self.collapse_ratio)

        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(LowPolyRock.bl_idname, icon='MOD_PARTICLES')


def register():
    bpy.utils.register_class(LowPolyRock)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
    bpy.utils.unregister_class(LowPolyRock)


if __name__ == "__main__":
    register()
