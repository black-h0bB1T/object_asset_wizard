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

import bpy, json, os, platform, subprocess

from bpy.types              import Operator
from bpy.props              import StringProperty, IntProperty, FloatProperty, BoolProperty

from . properties           import Properties
from . node_utils           import NodeUtils

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


    export_path: StringProperty()
    name: StringProperty()
    uv_map: StringProperty()
    dimensions: IntProperty()
    distance: FloatProperty()
    quality: IntProperty()
    render_margin: IntProperty()
    local: BoolProperty()


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
        scene.render.bake.margin = self.render_margin
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


    def create_ao_material(self):
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
        ao.samples = self.quality
        ao.only_local = self.local
        ao.inputs["Distance"].default_value = self.distance

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

        # Create the image.
        self.image = bpy.data.images.new(
            name=self.name, 
            width=self.dimensions, 
            height=self.dimensions,
            alpha=False, 
            float_buffer=False
        )
        self.image.file_format = 'PNG'
        self.image.filepath_raw = self.export_path

        # UV map node.
        uv = tree.nodes.new("ShaderNodeUVMap")
        uv.uv_map = self.uv_map

        # Image node.
        img = tree.nodes.new("ShaderNodeTexImage")
        img.image = self.image

        tree.links.new(uv.outputs["UV"], img.inputs["Vector"])


    def remove_ao_material(self):
        """
        Remove generated material from current scene.
        """
        bpy.data.materials.remove(self.material)
        bpy.data.images.remove(self.image)


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


    def bake(self, obj):
        """
        Bake AO map to the given (external) file.
        """
        self.store_settings()
        self.adjust_settings()

        self.create_ao_material()
        original = self.apply_material(obj)

        bpy.ops.object.bake(type='EMIT', save_mode='EXTERNAL')
        self.image.save()

        self.restore_materials(obj, original)
        self.remove_ao_material()
        self.restore_settings()


    def execute(self, context):
        # Output path must exist (does nothing if exists).
        path = os.path.split(self.export_path)[0]
        if not os.path.exists(path):
            os.makedirs(path)

        # Do the bake.
        self.bake(context.active_object)

        return {'FINISHED'}


class CurvatureMapOperator(Operator):
    """
    Calculates a curvature mask file using an external application.
    """
    bl_idname = "asset_wizard.calc_curvature_map_op"
    bl_label = "Calculate Curvature Map"
    bl_description = "Calculates the curvature map for the selected object"
    bl_options = {'REGISTER'}

    export_path: StringProperty()
    name: StringProperty()
    uv_map: StringProperty()    
    dimensions: IntProperty()
    analyze_mode: StringProperty()
    min_angle: IntProperty()
    line_thickness: IntProperty()
    apply_modifiers: BoolProperty()

    def export_mesh(self, obj, json_file):
        """
        Create input file for curvature tool.
        """
        m = obj.to_mesh(bpy.context.depsgraph, self.apply_modifiers)
        m.calc_normals()

        mesh = {
            "settings": {
                "mode": self.analyze_mode,
                "outputFile": self.export_path,
                "aoFile": "",
                "imageDimensions": self.dimensions,
                "lineThickness": self.line_thickness,
                "minAngle": float(self.min_angle) / 180.0
            },
            "uvs": [],
            "vertices": [],
            "faces": []
        }

        uvs = m.uv_layers[self.uv_map].data
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

        with open(json_file, "w") as f:
            json.dump(mesh, f, indent=4, separators=(',', ': '))

        bpy.data.meshes.remove(m)
    

    def execute(self, context):
        # Output path must exist (does nothing if exists).
        path = os.path.split(self.export_path)[0]
        if not os.path.exists(path):
            os.makedirs(path)
            
        json_file = os.path.splitext(self.export_path)[0] + ".json"
        self.export_mesh(context.active_object, json_file)

        if platform.system() == "Windows":
            exe = "curvature.exe"
        elif platform.system() == "Linux":
            exe = "curvature"
        else: # Darwin
            self.report({'ERROR'}, "Tool on your platform not available (yet)")
            return {'FINISHED'}

        curvtool = os.path.join(os.path.split(__file__)[0], "data", "tools", exe)
        cmd = [ curvtool, json_file ]
        print("Command: ", cmd)
        result = subprocess.Popen(cmd).wait()
        if result != 0:
            self.report({'ERROR'}, "Generation failed, see console")

        os.unlink(json_file)

        return {'FINISHED'}


class AoNodeOperator(Operator, NodeUtils):
    """
    Create AO map node
    """
    bl_idname = "asset_wizard.create_ao_node_op"
    bl_label = "Create AO Node"
    bl_description = "Generate AO node from current map settings"
    bl_options = {'REGISTER'}

    export_path: StringProperty()
    name: StringProperty()
    uv_map: StringProperty()

    def execute(self, context):
        # Access the current tree.
        group, input, output = self.create_group(context.space_data.edit_tree, self.name, 6)
        tree = group.node_tree

        # UV map node.
        uv = self.at(tree.nodes.new("ShaderNodeUVMap"), 1, 0)
        uv.uv_map = self.uv_map

        # Image node.
        img = self.at(self.create_image_node(tree, self.export_path), 2, 0)

        # Adjust nodes.
        sub = self.at(self.create_math_node(tree, 'SUBTRACT', True), 4, 0)
        diff = self.at(self.create_math_node(tree, 'SUBTRACT'), 5, 0)
        scale = self.at(self.create_math_node(tree, 'DIVIDE'), 5, -1)

        mn = self.create_group_input(group, input, "Float", "Min", 0.0)
        mx = self.create_group_input(group, input, "Float", "Max", 1.0)
        val = self.create_group_output(group, output, "Float", "Value")

        # Connect nodes.
        tree.links.new(uv.outputs["UV"], img.inputs["Vector"])
        tree.links.new(img.outputs["Color"], sub.inputs[0])
        tree.links.new(mn, sub.inputs[1])
        tree.links.new(mx, diff.inputs[0])
        tree.links.new(mn, diff.inputs[1])
        tree.links.new(sub.outputs["Value"], scale.inputs[0])
        tree.links.new(diff.outputs["Value"], scale.inputs[1])
        tree.links.new(scale.outputs["Value"], val)

        return {'FINISHED'}


class CurvatureNodeOperator(Operator, NodeUtils):
    """
    Create curvature map node
    """
    bl_idname = "asset_wizard.create_curvature_node_op"
    bl_label = "Create Curvature Node"
    bl_description = "Generate curvature node from current map settings"
    bl_options = {'REGISTER'}

    export_path: StringProperty()
    name: StringProperty()
    uv_map: StringProperty()    

    def execute(self, context):
        # Access the current tree.
        group, input, output = self.create_group(context.space_data.edit_tree, self.name, 8)
        tree = group.node_tree

        # UV map node.
        uv = self.at(tree.nodes.new("ShaderNodeUVMap"), 1, 0)
        uv.uv_map = self.uv_map

        # Image node.
        img = self.at(self.create_image_node(tree, self.export_path), 2, 0)

        # Split RGB
        split = self.at(tree.nodes.new("ShaderNodeSeparateRGB"), 4, 0)

        # Adjust nodes.
        subCx = self.at(self.create_math_node(tree, 'SUBTRACT', True), 5, 0)
        diffCx = self.at(self.create_math_node(tree, 'SUBTRACT'), 6, 0)
        scaleCx = self.at(self.create_math_node(tree, 'DIVIDE'), 7, -1)
        subCv = self.at(self.create_math_node(tree, 'SUBTRACT', True), 5, -2)
        diffCv = self.at(self.create_math_node(tree, 'SUBTRACT'), 6, -2)
        scaleCv = self.at(self.create_math_node(tree, 'DIVIDE'), 7, -3)

        mnCx = self.create_group_input(group, input, "Float", "Min Convex", 0.0)
        mxCx = self.create_group_input(group, input, "Float", "Max Convex", 1.0)
        valCx = self.create_group_output(group, output, "Float", "Convex")
        mnCv = self.create_group_input(group, input, "Float", "Min Concave", 0.0)
        mxCv = self.create_group_input(group, input, "Float", "Max Concave", 1.0)
        valCv = self.create_group_output(group, output, "Float", "Concave")

        # Connect nodes.
        tree.links.new(uv.outputs["UV"], img.inputs["Vector"])
        tree.links.new(img.outputs["Color"], split.inputs["Image"])
        tree.links.new(split.outputs["G"], subCx.inputs[0])
        tree.links.new(mnCx, subCx.inputs[1])
        tree.links.new(mxCx, diffCx.inputs[0])
        tree.links.new(mnCx, diffCx.inputs[1])
        tree.links.new(subCx.outputs["Value"], scaleCx.inputs[0])
        tree.links.new(diffCx.outputs["Value"], scaleCx.inputs[1])
        tree.links.new(scaleCx.outputs["Value"], valCx)
        tree.links.new(split.outputs["R"], subCv.inputs[0])
        tree.links.new(mnCv, subCv.inputs[1])
        tree.links.new(mxCv, diffCv.inputs[0])
        tree.links.new(mnCv, diffCv.inputs[1])
        tree.links.new(subCv.outputs["Value"], scaleCv.inputs[0])
        tree.links.new(diffCv.outputs["Value"], scaleCv.inputs[1])
        tree.links.new(scaleCv.outputs["Value"], valCv)

        return {'FINISHED'}

    
class MapGenerateUV(Operator):
    """
    Generate UV map for the selected object.
    """
    bl_idname = "asset_wizard.map_generate_uv_op"
    bl_label = "Generate UV Map"
    bl_description = "Generate UV map for AO and curvature, named NW_UVMap"
    bl_options = {'REGISTER'}

    island_margin: FloatProperty()

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

        print("Margin = ", self.island_margin)
        bpy.ops.uv.smart_project(
            island_margin=self.island_margin, 
            stretch_to_bounds=False
        )

        properties = Properties.get()
        properties.cao_uv_map = "NW_UVMap"

        return {'FINISHED'}


class UseObjectNameForMap(Operator):
    """
    Fills the name of the current object to the map name in CAO map generator.
    """
    bl_idname = "asset_wizard.use_object_name_for_map_op"
    bl_label = "Use Object Name"
    bl_description = "Use active object name as map name"
    bl_options = {'REGISTER'}    

    def execute(self, context):
        obj = context.active_object
        if not obj:
            return {'FINISHED'}

        Properties.get().cao_export_map_basename = obj.name

        return {'FINISHED'}
