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

import bpy, os
from bpy.types              import Operator
from bpy.props              import StringProperty, BoolProperty

from . texture_mapper       import TextureMapper
from . node_utils           import NodeUtils
from . properties           import Properties
from . utils                import blender_2_8x, export_file, ASSET_TYPE_MATERIAL
from . preferences          import PreferencesPanel

class GenerateBase(NodeUtils):
    """
    Generic methods to create PBR and Image node groups.
    """
    add_hslbc: BoolProperty()
    add_uv: BoolProperty()
    decal: BoolProperty()

    # Required for texture browser.
    filepath: StringProperty(subtype="FILE_PATH") 
    directory: StringProperty(name="Directory", subtype="DIR_PATH", default="", description="Folder to search in for image files")

    def create_texture_mapping(self, group, input, output, vectorInput, parentTree):
        """
        Create the texture mapping setup.
        """
        tree = group.node_tree

        if not vectorInput:
            texCoord = self.at(tree.nodes.new("ShaderNodeTexCoord"), 0, 2)

        separate = self.at(tree.nodes.new("ShaderNodeSeparateXYZ"), 2, 1)
        scaleX = self.at(self.create_math_node(tree, "MULTIPLY", def1 = 1.0), 3, 1)
        scaleY = self.at(self.create_math_node(tree, "MULTIPLY", def1 = 1.0), 3, 0)
        offsetX = self.at(self.create_math_node(tree, "ADD", def1 = 0.0), 4, 1)
        offsetY = self.at(self.create_math_node(tree, "ADD", def1 = 0.0), 4, 0)
        combine = self.at(tree.nodes.new("ShaderNodeCombineXYZ"), 5, 0)

        if not vectorInput:
            tree.links.new(texCoord.outputs["UV"], separate.inputs["Vector"])
        else:
            tree.links.new(self.create_group_input(group, input, "Vector", "Vector"), separate.inputs["Vector"])
            ptx = parentTree.nodes.new("ShaderNodeTexCoord")
            ptx.location.x = group.location.x - 3 * self.gridSizeX
            pm = parentTree.nodes.new("ShaderNodeMapping")
            pm.location.x = group.location.x - 2 * self.gridSizeX
            parentTree.links.new(ptx.outputs["UV"], pm.inputs["Vector"])
            parentTree.links.new(pm.outputs["Vector"], group.inputs["Vector"])

        tree.links.new(separate.outputs["X"], scaleX.inputs[0])
        tree.links.new(separate.outputs["Y"], scaleY.inputs[0])
        tree.links.new(scaleX.outputs["Value"], offsetX.inputs[0])
        tree.links.new(scaleY.outputs["Value"], offsetY.inputs[0])
        tree.links.new(offsetX.outputs["Value"], combine.inputs["X"])
        tree.links.new(offsetY.outputs["Value"], combine.inputs["Y"])

        scale = self.create_group_input(group, input, "Float", "Scale", 1.0)
        tree.links.new(scale, scaleX.inputs[1])
        tree.links.new(scale, scaleY.inputs[1])
        tree.links.new(self.create_group_input(group, input, "Float", "Offset X", 0.0), offsetX.inputs[1])
        tree.links.new(self.create_group_input(group, input, "Float", "Offset Y", 0.0), offsetY.inputs[1])

        return combine


    def create_hslbc(self, group, input, output, gridX, gridY, colorSocket, outputSockets):
        """
        Plugs a HSL and Brightness/Contrast-Node between colorSocket and outputSockets.
        """
        tree = group.node_tree
        hsl = self.at(tree.nodes.new("ShaderNodeHueSaturation"), gridX, gridY)
        bc = self.at(tree.nodes.new("ShaderNodeBrightContrast"), gridX + 0.5, gridY - 0.5)

        tree.links.new(self.create_group_input(group, input, "Float", "Hue", 0.5), hsl.inputs["Hue"])
        tree.links.new(self.create_group_input(group, input, "Float", "Saturation", 1.0), hsl.inputs["Saturation"])
        tree.links.new(self.create_group_input(group, input, "Float", "HSL-Value", 1.0), hsl.inputs["Value"])

        tree.links.new(self.create_group_input(group, input, "Float", "Brightness", 0.0), bc.inputs["Bright"])
        tree.links.new(self.create_group_input(group, input, "Float", "Contrast", 0.0), bc.inputs["Contrast"])

        tree.links.new(colorSocket, hsl.inputs["Color"])
        tree.links.new(hsl.outputs["Color"], bc.inputs["Color"])
        for s in outputSockets:
            tree.links.new(bc.outputs["Color"], s)


    def create_pbr_setup(self, group, input, output, mapper, vector, hslbc, decal):
        """
        Create the texture / shader setup.
        """
        tree = group.node_tree

        shader = self.at(tree.nodes.new("ShaderNodeBsdfPrincipled"), 10, 1)
        tree.links.new(shader.outputs["BSDF"], self.create_group_output(group, output, "Shader", "Shader"))

        gridPos = 3

        # Diffuse in any case ..
        diffuse = self.at(self.create_image_node(tree, mapper.diffuse, False, decal), 6, gridPos)
        tree.links.new(vector.outputs["Vector"], diffuse.inputs["Vector"])
        if hslbc:
            self.create_hslbc(group, input, output, 8, gridPos, diffuse.outputs["Color"], [
                shader.inputs["Base Color"],
                self.create_group_output(group, output, "Color", "Base Color")
            ])
        else:
            tree.links.new(diffuse.outputs["Color"], shader.inputs["Base Color"])
            tree.links.new(diffuse.outputs["Color"], self.create_group_output(group, output, "Color", "Base Color"))
        tree.links.new(diffuse.outputs["Alpha"], self.create_group_output(group, output, "Float", "Alpha"))
        gridPos -= 2

        # Metallic if available.
        if mapper.metal != None:
            metal = self.at(self.create_image_node(tree, mapper.metal, clip = decal), 6, gridPos)
            tree.links.new(vector.outputs["Vector"], metal.inputs["Vector"])
            tree.links.new(metal.outputs["Color"], shader.inputs["Metallic"])
            tree.links.new(metal.outputs["Color"], self.create_group_output(group, output, "Float", "Metallic"))
            gridPos -= 2

        # Specular if available.
        if mapper.specular != None:
            specular = self.at(self.create_image_node(tree, mapper.specular, clip = decal), 6, gridPos)
            tree.links.new(vector.outputs["Vector"], specular.inputs["Vector"])
            tree.links.new(specular.outputs["Color"], shader.inputs["Specular"])
            tree.links.new(specular.outputs["Color"], self.create_group_output(group, output, "Float", "Specular"))
            gridPos -= 2

        # Create the wet factor to the roughness.
        wet = self.at(self.create_math_node(tree, "SUBTRACT", True, def1 = 0.0), 9, gridPos)
        tree.links.new(wet.outputs["Value"], shader.inputs["Roughness"])
        tree.links.new(wet.outputs["Value"], self.create_group_output(group, output, "Float", "Roughness"))
        tree.links.new(self.create_group_input(group, input, "Float", "Wet Intensity", 0.0), wet.inputs[1])

        # Prefer roughness if available, otherwise try gloss.
        if mapper.roughness != None:
            roughness = self.at(self.create_image_node(tree, mapper.roughness, clip = decal), 6, gridPos)
            tree.links.new(vector.outputs["Vector"], roughness.inputs["Vector"])
            tree.links.new(roughness.outputs["Color"], wet.inputs[0])
        elif mapper.gloss != None:
            gloss = self.at(self.create_image_node(tree, mapper.gloss, clip = decal), 6, gridPos)
            tree.links.new(vector.outputs["Vector"], gloss.inputs["Vector"])
            roughness = self.at(self.create_math_node(tree, "SUBTRACT", def0 = 1.0), 8, gridPos)
            tree.links.new(gloss.outputs["Color"], roughness.inputs[1])
            tree.links.new(roughness.outputs["Value"], wet.inputs[0])
        gridPos -= 2

        # Normal or height if available.
        if mapper.normal != None:
            normal = self.at(self.create_image_node(tree, mapper.normal, clip = decal), 6, gridPos)
            tree.links.new(vector.outputs["Vector"], normal.inputs["Vector"])
            nvector = self.at(tree.nodes.new("ShaderNodeNormalMap"), 8, gridPos)
            tree.links.new(normal.outputs["Color"], nvector.inputs["Color"])
            tree.links.new(nvector.outputs["Normal"], shader.inputs["Normal"])
            tree.links.new(nvector.outputs["Normal"], self.create_group_output(group, output, "Vector", "Normal"))
        elif mapper.height != None:
            height = self.at(self.create_image_node(tree, mapper.height, clip = decal), 6, gridPos)
            tree.links.new(vector.outputs["Vector"], height.inputs["Vector"])
            nvector = self.at(tree.nodes.new("ShaderNodeBump"), 8, gridPos)
            tree.links.new(height.outputs["Color"], nvector.inputs["Height"])
            tree.links.new(self.create_group_input(group, input, "Float", "Bump Strength", 1.0), nvector.inputs["Strength"])
            tree.links.new(nvector.outputs["Normal"], shader.inputs["Normal"])
            tree.links.new(nvector.outputs["Normal"], self.create_group_output(group, output, "Vector", "Normal"))
        gridPos -= 2


    def create_image_setup(self, group, input, output, texture, vector, hslbc, decal):
        """
        Create the texture / shader setup.
        """
        tree = group.node_tree

        shader = self.at(tree.nodes.new("ShaderNodeBsdfPrincipled"), 15, 1)
        tree.links.new(shader.outputs["BSDF"], self.create_group_output(group, output, "Shader", "Shader"))

        gridPos = 3

        # Diffuse is set to non-color (for better processing the other maps) and 
        # a gamma=2.2 node is used to do non-color -> color transformation.
        diffuse = self.at(self.create_image_node(tree, texture, clip = decal), 6, gridPos)
        tree.links.new(vector.outputs["Vector"], diffuse.inputs["Vector"])
        gamma = self.at(tree.nodes.new("ShaderNodeGamma"), 8, gridPos)
        gamma.inputs["Gamma"].default_value = 2.2 
        tree.links.new(diffuse.outputs["Color"], gamma.inputs["Color"])
        if hslbc:
            self.create_hslbc(group, input, output, 10, gridPos, gamma.outputs["Color"], [
                shader.inputs["Base Color"],
                self.create_group_output(group, output, "Color", "Base Color")
            ])
        else:
            tree.links.new(gamma.outputs["Color"], shader.inputs["Base Color"])
            tree.links.new(gamma.outputs["Color"], self.create_group_output(group, output, "Color", "Base Color"))
        tree.links.new(diffuse.outputs["Alpha"], self.create_group_output(group, output, "Float", "Alpha"))
        gridPos -= 2

        # Create the wet factor to the roughness.
        wet = self.at(self.create_math_node(tree, "SUBTRACT", True, def1 = 0.0), 13, gridPos - 2.5)
        tree.links.new(wet.outputs["Value"], shader.inputs["Roughness"])
        tree.links.new(wet.outputs["Value"], self.create_group_output(group, output, "Float", "Roughness"))
        tree.links.new(self.create_group_input(group, input, "Float", "Wet Intensity", 0.0), wet.inputs[1])

        rouIn, rouOut = self.create_range_selector(group, input, 8, gridPos, "Roughness")
        tree.links.new(diffuse.outputs["Color"], rouIn)
        tree.links.new(rouOut, wet.inputs[0])
        gridPos -= 2

        heiIn, heiOut = self.create_range_selector(group, input, 8, gridPos, "Normal")
        tree.links.new(diffuse.outputs["Color"], heiIn)
        tree.links.new(heiOut, self.create_group_output(group, output, "Float", "Height"))
        bump = self.at(tree.nodes.new("ShaderNodeBump"), 13, gridPos - 2.5)
        tree.links.new(heiOut, bump.inputs["Height"])
        tree.links.new(self.create_group_input(group, input, "Float", "Bump Strength", 0.25), bump.inputs["Strength"])
        tree.links.new(bump.outputs["Normal"], shader.inputs["Normal"])
        tree.links.new(bump.outputs["Normal"], self.create_group_output(group, output, "Vector", "Normal"))
        gridPos -= 2

 
class GeneratePBROperator(Operator, GenerateBase):
    bl_idname = "asset_wizard.generate_pbr_op"
    bl_label = "PBR"
    bl_description = "Generate PBR node group from selected image. Just select one image from a PBR image set." 
    bl_options = {'REGISTER', 'UNDO'}


    def execute(self, context):
        """ 
        Called after the user has choosen a texture file, the setup is created in here.
        """
        # Access the current tree.
        tree = context.space_data.edit_tree

        # Automatically map texture names ...
        mapper = TextureMapper(self.filepath)
        if not mapper.valid:
            self.report({"ERROR"}, "Can't find any valid diffuse texture, try to modify valid extensions (nw_texture_mapper.py) ...")
            return {'CANCELLED'} 

        # Create and fill the group.
        group, input, output = self.create_group(tree, mapper.baseName, 12)
        vector = self.create_texture_mapping(group, input, output, self.add_uv, tree)
        self.create_pbr_setup(group, input, output, mapper, vector, self.add_hslbc, self.decal)

        return {'FINISHED'}

        
    def invoke(self, context, event):
        """
        Opens the texture selection file browser.
        """
        # Start at texture directory the first time.
        if len(self.directory) == 0:
            self.directory = context.preferences.filepaths.texture_directory

        context.window_manager.fileselect_add(self) 

        return {'RUNNING_MODAL'}    


class GenerateImageOperator(Operator, GenerateBase):
    bl_idname = "asset_wizard.generate_image_op"
    bl_label = "Image"
    bl_description = "Generate PBR node group from selected image. Select a diffuse map, " + \
        "roughness and normal maps are extracted from it." 
    bl_options = {'REGISTER', 'UNDO'}

             
    def execute(self, context):
        """ 
        Called after the user has choosen a texture file, the setup is created in here.
        """
        # Access the current tree.
        tree = context.space_data.edit_tree

        baseName = os.path.splitext(os.path.split(self.filepath)[1])[0]

        # Create and fill the group.
        group, input, output = self.create_group(tree, baseName, 17)
        vector = self.create_texture_mapping(group, input, output, self.add_uv, tree)
        self.create_image_setup(group, input, output, self.filepath, vector, self.add_hslbc, self.decal)

        return {'FINISHED'}

        
    def invoke(self, context, event):
        """
        Opens the texture selection file browser.
        """
        # Start at texture directory the first time.
        if len(self.directory) == 0:
            self.directory = context.preferences.filepaths.texture_directory

        context.window_manager.fileselect_add(self) 

        return {'RUNNING_MODAL'}


class ExportPBROperator(Operator, GenerateBase):
    bl_idname = "asset_wizard.export_pbr_op"
    bl_label = "PBR and export"
    bl_description = "Generate PBR node group from selected image. Just select one image from a PBR image set. " + \
        "The node is stored as material in an asset blend file using the base texture name in the current category."
    bl_options = {'REGISTER', 'UNDO'}        


    category: StringProperty()    


    def execute(self, context):
        """ 
        Called after the user has choosen a texture file, the setup is created in here.
        """
        # Automatically map texture names ...
        mapper = TextureMapper(self.filepath)
        if not mapper.valid:
            self.report({"ERROR"}, "Can't find any valid diffuse texture, try to modify valid extensions (nw_texture_mapper.py) ...")
            return {'CANCELLED'} 

        mat = bpy.data.materials.new(mapper.baseName)
        # Enforce name
        mat.name = mapper.baseName
        mat.use_nodes = True

        # Access the current tree.
        tree = mat.node_tree

        # Remove existing nodes.
        nodes = [ n for n in tree.nodes ]
        [ tree.nodes.remove(n) for n in nodes ]

        # Create and fill the group.
        group, input, output = self.create_group(tree, mapper.baseName, 12)
        vector = self.create_texture_mapping(group, input, output, self.add_uv, tree)
        self.create_pbr_setup(group, input, output, mapper, vector, self.add_hslbc, self.decal)

        # Create and connect output node.
        output = tree.nodes.new("ShaderNodeOutputMaterial")
        output.location.x += 200
        tree.links.new(group.outputs["Shader"], output.inputs["Surface"])

        # Export to file.
        filename = export_file(ASSET_TYPE_MATERIAL, self.category, mapper.baseName, ".blend")
        if blender_2_8x():
            bpy.data.libraries.write(
                filename, 
                set([mat, ]), 
                relative_remap=True, 
                compress=True,
                fake_user=True
            )
        else:
            bpy.data.libraries.write(
                filename, 
                set([mat, ]), 
                path_remap=PreferencesPanel.get().export_remap, 
                compress=True,
                fake_user=True
            )        

        self.report({'INFO'}, "Material written to: " + filename)

        # Remove generated material from current scene.
        bpy.data.materials.remove(mat)

        # Refresh view.
        bpy.ops.asset_wizard.refresh_material_previews_op()

        # Put onto render queue.
        Properties.get_render_previews().add_job(
            ASSET_TYPE_MATERIAL, 
            filename
        )

        return {'FINISHED'}

        
    def invoke(self, context, event):
        """
        Opens the texture selection file browser.
        """
        # Start at texture directory the first time.
        if len(self.directory) == 0:
            self.directory = context.preferences.filepaths.texture_directory

        context.window_manager.fileselect_add(self) 

        return {'RUNNING_MODAL'}   


class ExportMaterialOperator(Operator):
    bl_idname = "asset_wizard.export_material_op"
    bl_label = "Export Material"
    bl_description = "Exports the current material to an asset blend to the active category. Material is used as file name"
    bl_options = {'REGISTER'}  


    category: StringProperty()    


    def execute(self, context):
        # Get active material.
        mat = context.active_object.active_material

        # Export to file.
        filename = export_file(ASSET_TYPE_MATERIAL, self.category, mat.name, ".blend")
        if blender_2_8x():
            bpy.data.libraries.write(
                filename, 
                set([mat, ]), 
                relative_remap=True, 
                compress=True,
                fake_user=True
            )
        else:
            bpy.data.libraries.write(
                filename, 
                set([mat, ]), 
                path_remap=PreferencesPanel.get().export_remap, 
                compress=True,
                fake_user=True
            ) 

        self.report({'INFO'}, "Material written to: " + filename)       

        # Refresh view.
        bpy.ops.asset_wizard.refresh_material_previews_op()

        # Put onto render queue.
        Properties.get_render_previews().add_job(
            ASSET_TYPE_MATERIAL, 
            filename
        )        

        return {'FINISHED'} 
