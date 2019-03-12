# Copyright (C) 2019 h0bB1T
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
#
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA

import bpy, json

from bpy.types              import Operator

from . properties           import Properties

class BakeAoMapOperator(Operator):
    """
    Render AO map by creating a temporary material which outputs the AO
    as emission and bake the emission map.
    A single object with a non overlapping UV map must be selected!
    """
    bl_idname = "asset_wizard.bake_ao_map_op"
    bl_label = "Bake AO Map"
    bl_description = "Bakes an AO map of the selected (single) object, which must have a non-" + \
        " overlapping UV map"
    bl_options = {'REGISTER'}

    def store_settings(self):
        """
        Store render and bake settings.
        """
        scene = bpy.context.scene
        self.engine = scene.render.engine
        self.use_bake_multires = scene.render.use_bake_multires
        self.bake_type = scene.cycles.bake_type
        self.margin = scene.render.bake.margin
        self.use_clear = scene.render.bake.use_clear
        self.use_selected_to_active = scene.render.bake.use_selected_to_active


    def adjust_settings(self):
        """
        Set render and bake settings as we need it.
        """
        scene = bpy.context.scene
        scene.render.engine = 'CYCLES'
        scene.render.use_bake_multires = False
        scene.cycles.bake_type = 'EMIT' 
        scene.render.bake.margin = 16
        scene.render.bake.use_clear = True
        scene.render.bake.use_selected_to_active = False


    def restore_settings(self):
        """
        Restore render and bake settings.
        """
        scene = bpy.context.scene
        scene.render.bake.use_selected_to_active = self.use_selected_to_active
        scene.render.bake.use_clear = self.use_clear
        scene.render.bake.margin = self.margin
        scene.cycles.bake_type = self.bake_type 
        scene.render.use_bake_multires = self.use_bake_multires
        scene.render.engine = self.engine


    def create_ao_material(self, samples, distance, dimension, outputfile):
        """
        Create material that we bake.
        """
        self.material = bpy.data.materials.new("__NW_AO__")
        self.material.use_nodes = True

        # Access the current tree.
        tree = self.material.node_tree

        # Remove existing nodes.
        nodes = [ n for n in tree.nodes ]
        [ tree.nodes.remove(n) for n in nodes ]

        # Create AO node.
        ao = tree.nodes.new("ShaderNodeAmbientOcclusion")
        ao.samples = samples
        ao.only_local = True
        ao.inputs["Distance"].default_value = distance

        # Invert color.
        invert = tree.nodes.new("ShaderNodeInvert")

        # Emission Shader.
        emit = tree.nodes.new("ShaderNodeEmission")

        # Create and connect output node.
        output = tree.nodes.new("ShaderNodeOutputMaterial")

        # Connect the nodes.
        tree.links.new(ao.outputs["Color"], invert.inputs["Color"])
        tree.links.new(invert.outputs["Color"], emit.inputs["Color"])
        tree.links.new(emit.outputs["Emission"], output.inputs["Surface"])

        self.image = bpy.data.images.new(
            name=outputfile, 
            width=dimension, 
            height=dimension,
            alpha=False, 
            float_buffer=False
        )
        self.image.file_format = 'PNG'
        self.image.filepath_raw = outputfile

        img = tree.nodes.new("ShaderNodeTexImage")
        img.image = self.image


    def remove_ao_material(self):
        """
        Remove generated material from current scene.
        """
        bpy.data.materials.remove(self.material)


    def apply_material(self, obj):
        """
        Apply the AO generation material to the given object.
        """
        original = []
        if len(obj.material_slots) > 0:
            for i, s in enumerate(obj.material_slots):
                original.append(s.material)
                obj.material_slots[i].material = self.material
        else:
            obj.data.materials.append(self.material)

        return original


    def restore_materials(self, obj, original):
        """
        Restore materials from current object.
        """
        if original:
            for i, m in enumerate(original):
                obj.material_slots[i].material = original[i]
        else:
            obj.data.materials.pop(index=0)


    def bake(self, obj, dimension, outputfile):
        """
        Bake AO map to the given (external) file.
        """
        self.store_settings()
        self.adjust_settings()

        self.create_ao_material(16, 0.25, dimension, outputfile)
        original = self.apply_material(obj)

        bpy.ops.object.bake(type='EMIT', save_mode='EXTERNAL')
        self.image.save()

        self.restore_materials(obj, original)
        self.remove_ao_material()
        self.restore_settings()

    
    def create_node(self):
        pass


    def execute(self, context):
        self.bake(
            context.active_object,
            1024,
            "c:/tmp/test_ao.png"
        )

        return {'FINISHED'}


class CurvatureMapOperator(Operator):
    """
    Calculates a curvature mask file using an external application.
    """
    bl_idname = "asset_wizard.calc_curvature_map_op"
    bl_label = "Calculate Curvature Map"
    bl_description = "Calculates the curvature map for the selected object"
    bl_options = {'REGISTER'}

    def export_mesh(self, filename, obj):
        """
        Create input file for curvature tool.
        """
        m = bpy.context.object.to_mesh(bpy.context.depsgraph, True)
        m.calc_normals()

        mesh = {
            "settings": {
                "mode": "Deep",
                "outputFile": "c:/tmp/curvature.png",
                "aoFile": "c:/tmp/test_ao.png",
                "imageDimensions": 2048,
                "lineThickness": 16,
                "minAngle": 0.05
            },
            "uvs": [],
            "vertices": [],
            "faces": []
        }

        uvs = m.uv_layers[0].data
        for v in uvs:
            mesh["uvs"].append((v.uv[0], v.uv[1]))
            
        for v in m.vertices:
            mesh["vertices"].append((v.co[0], v.co[1], v.co[2]))

        for f in m.polygons:
            mesh["faces"].append({
                "normal": [ v for v in f.normal ],
                "uv": [ v for v in f.loop_indices ],
                "vertices": [ v for v in f.vertices ]
            })

        with open(filename, "w") as f:
            json.dump(mesh, f, indent=4, separators=(',', ': '))

        bpy.data.meshes.remove(m)
    

    def execute(self, context):
        self.export_mesh(
            "c:/tmp/curvature.json",
            context.active_object
            )

        return {'FINISHED'}


class AoNodeOperator(Operator):
    """
    Create AO map node
    """
    bl_idname = "asset_wizard.create_ao_node_op"
    bl_label = "Create AO Node"
    bl_description = "Generate AO node from current map settings"
    bl_options = {'REGISTER'}

    def execute(self, context):

        return {'FINISHED'}


class CurvatureNodeOperator(Operator):
    """
    Create curvature map node
    """
    bl_idname = "asset_wizard.create_curvature_node_op"
    bl_label = "Create Curvature Node"
    bl_description = "Generate curvature node from current map settings"
    bl_options = {'REGISTER'}

    def execute(self, context):

        return {'FINISHED'}

    
class MapGenerateUV(Operator):
    """
    Generate UV map for the selected object.
    """
    bl_idname = "asset_wizard.map_generate_uv_op"
    bl_label = "Generate UV Map"
    bl_description = "Generate UV map for AO and curvature, named NW_UVMap"
    bl_options = {'REGISTER'}

    def execute(self, context):
        obj = context.active_object
        if not obj:
            return {'FINISHED'}

        # Create if doesn't exist.
        idx = obj.data.uv_layers.find("NW_UVMap")
        if obj.data.uv_layers.find("NW_UVMap") == -1:
            obj.data.uv_layers.active = obj.data.uv_layers.new(name="NW_UVMap")
        else:
            obj.data.uv_layers.active_index = idx        

        bpy.ops.uv.smart_project(island_margin=0.01, stretch_to_bounds=False)

        properties = Properties.get()
        properties.cao_uv_map = "NW_UVMap"

        return {'FINISHED'}
