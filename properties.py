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
from bpy.props import EnumProperty, BoolProperty, IntProperty, PointerProperty, StringProperty
from bpy.types import PropertyGroup, WindowManager

from . utils                import (categories, list_to_enum, 
                                        ASSET_TYPE_OBJECT, ASSET_TYPE_MATERIAL,
                                        ASSET_TYPE_NODES, ASSET_TYPE_NODES_MATERIALS)
from . preview_helper       import PreviewHelper

class Properties(PropertyGroup):
    export_location_type = (
        ('0', "Original", "Leave object positions untouched"), 
        ('1', "Origin", "Center objects based on bounding box"), 
        ('2', "Origin Z=0", "Center objects based on bounding box, but place lower plane on Z=0")
    )

    export_rename_type = (
        ('0', "Original", "Leave name untouched"), 
        ('1', "Prefix", "Prefix name with [AssetName]_"), 
        ('2', "Full", "Replace name with [AssetName]_[NNN]")
    )

    export_type = (
        ('0', "Blend", "Export in Blender file format"), 
        ('1', "FBX", "Export in FBX file format"), 
    )

    import_location_type = (
        ('0', "Origin", ""), 
        ('1', "Cursor", ""), 
        ('2', "Cursor/XY", "")
    )


    # Export object properties.
    eobj_categories: EnumProperty(
        name="", 
        items=lambda _, __: list_to_enum(categories(ASSET_TYPE_OBJECT))
        )
    eobj_asset_name: StringProperty(name="", default="Asset")
    eobj_location: EnumProperty(
        name="Location", 
        items=export_location_type, 
        default="2"
        )
    eobj_rotation: BoolProperty(
        name="Clear Rotation", 
        description="Reset XYZ rotation, single selection only", 
        default=True
        )
    eobj_rename: EnumProperty(name="Rename", items=export_rename_type, default="2")
    eobj_rename_material: EnumProperty(name="Rename", items=export_rename_type, default="2")
    eobj_export_type: EnumProperty(name="Export", items=export_type)
    eobj_new_category: StringProperty(name="", description="Put new category name in here")


    # Import properties.
    iobj_categories: EnumProperty(
        name="", 
        description="Object category",
        items=lambda _, __: list_to_enum(categories(ASSET_TYPE_OBJECT)),
        update=lambda self, __: PreviewHelper.setData(ASSET_TYPE_OBJECT, (ASSET_TYPE_OBJECT, self.iobj_categories))
    )
    iobj_previews: EnumProperty(
        items=lambda _, __: PreviewHelper.getCollection(ASSET_TYPE_OBJECT).items
    )
    imat_categories: EnumProperty(
        name="", 
        description="Material category",
        items=lambda _, __: list_to_enum(categories(ASSET_TYPE_MATERIAL)),
        update=lambda self, __: PreviewHelper.setData(ASSET_TYPE_MATERIAL, (ASSET_TYPE_MATERIAL, self.imat_categories))
    )
    imat_previews: EnumProperty(
        items=lambda _, __: PreviewHelper.getCollection(ASSET_TYPE_MATERIAL).items
    )


    # Node wizard property.
    nw_add_hslbc: BoolProperty(name="Add HSL/BC", description="Add HSL and Brightness/Contrast inputs", default=True)
    nw_add_uv: BoolProperty(name="UV Input", description="Add external UV input instead of internally using primary UV mapping")
    nw_decal: BoolProperty(name="Clip Texture", description="Set textures to 'CLIP', so they can be used as decal")
    
    nw_nodes_previews: EnumProperty(
        items=lambda _, __: PreviewHelper.getCollection(ASSET_TYPE_NODES).items
    )
    nw_materials_previews: EnumProperty(
        items = lambda _, __: PreviewHelper.getCollection(ASSET_TYPE_NODES_MATERIALS).items
    )        
    
    nw_categories: EnumProperty(
        name="", 
        items=lambda _, __: list_to_enum(categories(ASSET_TYPE_MATERIAL))
    )
    nw_new_category: StringProperty(name="", description="Put new category name in here")


    @staticmethod
    def initialize():
        from . render_previews_ops  import RenderPreviews
        WindowManager.asset_wizard_properties = PointerProperty(type=Properties)
        WindowManager.asset_wizard_render_previews = RenderPreviews()


    @staticmethod
    def get():
        return bpy.context.window_manager.asset_wizard_properties       


    @staticmethod
    def get_render_previews():
        return bpy.context.window_manager.asset_wizard_render_previews


    @staticmethod
    def cleanup():
        del(WindowManager.asset_wizard_render_previews)
        del(WindowManager.asset_wizard_properties)


    @staticmethod
    def export_type_ext(export_type):
        """
        Get file extension for specified "export_type" (see above).
        """
        if export_type == '0':
            return ".blend"
        if export_type == '1':
            return ".fbx"
        return ".unknown"

