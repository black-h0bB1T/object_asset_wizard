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

from . utils                import textures_of_objects, blender_2_8x, export_file, ASSET_TYPE_OBJECT
from . common_utils         import calc_bounding_box
from . properties           import Properties
from . preferences          import PreferencesPanel
from . execute_blender      import run_blend_fix

class UseObjectNameOperator(Operator):
    bl_idname = "asset_wizard.use_object_name_op"
    bl_description = "Use name from active object."
    bl_label = "Use object name"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        if context.active_object:
            Properties.get()["eobj_asset_name"] = context.active_object.name
        return {'FINISHED'}

class ExportObjectBase:
    category: StringProperty()
    asset_name: StringProperty()
    pack_textures: BoolProperty()
    location: StringProperty()
    rotation: BoolProperty()
    rename: StringProperty()
    rename_material: StringProperty()
    export_type: StringProperty()


class OverwriteObjectExporterOperator(Operator, ExportObjectBase):
    bl_idname = "asset_wizard.overwrite_object_exporter_op"
    bl_label = "Overwrite existing file?"
    bl_description = "Export selected objects (file already exists)."
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        bpy.ops.asset_wizard.object_exporter_op(
            category = self.category,
            asset_name = self.asset_name,
            pack_textures = self.pack_textures,
            location = self.location,
            rotation = self.rotation,
            rename = self.rename,
            rename_material = self.rename_material,
            export_type = self.export_type
        )


        return {'FINISHED'}

    def draw(self, context):
        properties = Properties.get()

        layout = self.layout
        rows = min(20, len(properties.eobj_pack_textures_list))
        layout.row().template_list(
            "UI_UL_TexturePackList",
            "PackList",
            properties,
            "eobj_pack_textures_list",
            properties,
            "eobj_pack_textures_index",
            rows=rows,
            maxrows=rows
        )


    def invoke(self, context, event):
        if self.export_type == '0' and self.pack_textures and len(textures_of_objects(context.selected_objects)) > 0:
            properties = Properties.get()

            properties.eobj_pack_textures_list.clear()
            for m in textures_of_objects(context.selected_objects):
                properties.eobj_pack_textures_list.add().name = m

            return context.window_manager.invoke_props_dialog(self, width=800)
        else:
            return context.window_manager.invoke_confirm(self, event)    


class TexturePackSelectionOperator(Operator, ExportObjectBase):
    bl_idname = "asset_wizard.texture_selection_op"
    bl_label = "Select textures to pack"
    bl_description = "Export selected objects"
    bl_options = {'REGISTER', 'INTERNAL'}

    
    def invoke(self, context, event):
        properties = Properties.get()

        properties.eobj_pack_textures_list.clear()
        for m in textures_of_objects(context.selected_objects):
            properties.eobj_pack_textures_list.add().name = m

        return context.window_manager.invoke_props_dialog(self, width=800)


    def draw(self, context):
        properties = Properties.get()

        layout = self.layout
        rows = min(20, len(properties.eobj_pack_textures_list))
        layout.row().template_list(
            "UI_UL_TexturePackList",
            "PackList",
            properties,
            "eobj_pack_textures_list",
            properties,
            "eobj_pack_textures_index",
            rows=rows,
            maxrows=rows
        )


    def execute(self, context):
        bpy.ops.asset_wizard.object_exporter_op(
            category = self.category,
            asset_name = self.asset_name,
            pack_textures = self.pack_textures,
            location = self.location,
            rotation = self.rotation,
            rename = self.rename,
            rename_material = self.rename_material,
            export_type = self.export_type
        )

        return {'FINISHED'}        


class ObjectExporterOperator(Operator, ExportObjectBase):
    bl_idname = "asset_wizard.object_exporter_op"
    bl_label = "Export"
    bl_description = "Export selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    def calc_offset(self, objects):
        """
        Depending on export location, calculate and return the XYZ offset.
        """
        if self.location == "0": # Original
            return (0, 0, 0)

        bmin, bmax = calc_bounding_box(objects)
        center = (
            (bmax[0]-bmin[0])/2 + bmin[0],
            (bmax[1]-bmin[1])/2 + bmin[1],
            (bmax[2]-bmin[2])/2 + bmin[2]
        )

        if self.location == "1": # Origin
            return (-center[0], -center[1], -center[2])

        if self.location == "2": # Origin, Z == 0
            return (-center[0], -center[1], -bmin[2])


    def material_list(self, objects):
        """
        Create unique list of materials used by the objects.
        """
        l = []
        for o in objects:
            [ l.append(m.material) for m in o.material_slots if m.material ]
        return set(l)


    def store_object_information(self, objects):
        """
        Store (eventually) changed original values for later restoration.
        Returns dict with object: (name, meshName, originalPos, originalRot).
        """
        original = {}
        for o in objects:
            original[o] = (
                o.name,
                o.data.name if o.data else None,
                (o.location.x, o.location.y, o.location.z),
                (o.rotation_euler.x, o.rotation_euler.y, o.rotation_euler.z)
            )
        return original


    def restore_object_information(self, original):
        """
        Return objects to their original location.
        """
        for o in original.keys():
            name, mname, loc, rot = original[o]
            o.name = name
            if o.data:
                o.data.name = mname
            o.location = loc
            o.rotation_euler.x, o.rotation_euler.y, o.rotation_euler.z = rot


    def store_material_information(self, objects):
        """
        Store original material names.
        Returns dict with material: name.
        """
        original = {}
        for m in self.material_list(objects):
            original[m] = m.name
        return original


    def restore_material_information(self, original):
        """
        Restores the original names of the material.
        """
        for m in original.keys():
            m.name = original[m]


    def clear_rotation(self, objects):
        """
        If single object is selected, temporary clear it's rotation.
        """
        if self.rotation and len(objects) == 1:
            bpy.ops.object.rotation_clear(False)


    def translate_objects(self, objects, offset):
        """
        Move all objects by the offset, clears rotation, returns dictionary
        """
        for o in objects:
            o.location.x += offset[0]
            o.location.y += offset[1]
            o.location.z += offset[2]


    def rename_objects(self, objects):
        """
        Fix names according to setting.
        """
        if self.rename == "1": # Prefix
            for o in objects:
                o.name = "%s_%s" % (self.asset_name, o.name)
                if o.data:
                    o.data.name = o.name

        if self.rename == "2": # Full
            for i, o in enumerate(objects):
                o.name = "%s_%03i" % (self.asset_name, i)
                if o.data:
                    o.data.name = o.name


    def rename_materials(self, objects):
        """
        Fix names according to setting.
        """
        if self.rename_material == "1": # Prefix
            for m in self.material_list(objects):
                m.name = "%s_%s" % (self.asset_name, m.name)

        if self.rename_material == "2": # Full
            for i, m in enumerate(self.material_list(objects)):
                m.name = "%s_%03i" % (self.asset_name, i)


    def export_blend(self, path, objects):
        if blender_2_8x():
            bpy.data.libraries.write(
                path, 
                set(objects), 
                relative_remap=True, 
                compress=True,
                fake_user=True
            )
        else:
            bpy.data.libraries.write(
                path, 
                set(objects), 
                path_remap=PreferencesPanel.get().export_remap, 
                compress=True,
                fake_user=True
            )

        properties = Properties.get()
        textures_to_pack = [ os.path.split(t.name)[1] for t in properties.eobj_pack_textures_list if t.selected ]

        # The created file is just a library, instance the object using an external blender run.
        # https://blender.stackexchange.com/questions/129592/bpy-data-libraries-write-not-working
        run_blend_fix(path, textures_to_pack)


    def export_fbx(self, path):
        bpy.ops.export_scene.fbx(filepath=path, use_selection=True)


    def execute(self, context):
        # Get selected objects.
        objects = context.selected_objects

        # At least one must be selected.
        if not objects:
            self.report({'ERROR'}, "No object selected")

        # Store original state.
        original = self.store_object_information(objects)
        originalMat = self.store_material_information(objects)

        # Optionally reset rotation.
        self.clear_rotation(objects)

        # Optionally center object.
        self.translate_objects(objects, self.calc_offset(objects))

        # Optionally rename objects.
        self.rename_objects(objects)

        # Optionally rename materials.
        self.rename_materials(objects)

        # Do the export
        path = export_file(
            ASSET_TYPE_OBJECT,
            self.category, 
            self.asset_name, 
            Properties.export_type_ext(self.export_type)
            )
        if self.export_type == '0': # Blend
            self.export_blend(path, objects)
            self.report({'INFO'}, "BLEND created and fixed.")
        elif self.export_type == '1': # FBX
            self.export_fbx(path)
            self.report({'INFO'}, "FBX created.")

        # Restore original state.
        self.restore_material_information(originalMat)
        self.restore_object_information(original)

        # Refresh view.
        bpy.ops.asset_wizard.refresh_object_previews_op()

        # Put onto render queue.
        Properties.get_render_previews().add_job(
            ASSET_TYPE_OBJECT, 
            path
        )
        
        return {'FINISHED'}
