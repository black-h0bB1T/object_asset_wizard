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
from bpy.props import EnumProperty, BoolProperty, IntProperty, PointerProperty, StringProperty, FloatProperty, CollectionProperty
from bpy.types import PropertyGroup, WindowManager

from . utils                import (categories, categories_enum, 
                                        ASSET_TYPE_OBJECT, ASSET_TYPE_MATERIAL,
                                        ASSET_TYPE_NODES, ASSET_TYPE_NODES_MATERIALS)
from . preview_helper       import PreviewHelper
from . preview_parsers      import CollectionImageParser

class TexturesToExport(PropertyGroup):
    selected: BoolProperty()
    name: StringProperty()


class UI_UL_TexturePackList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # We could write some code to decide which icon to use here... 
        custom_icon = 'OBJECT_DATAMODE'
        
        # Make sure your code supports all 3 layout types 
        if self.layout_type in {'DEFAULT', 'COMPACT'}: 
            p, n = os.path.split(item.name)
            layout.prop(item, "selected", text=f"{n}  --  {p}", toggle=True) 
        elif self.layout_type in {'GRID'}: 
            layout.alignment = 'CENTER' 
            layout.label(text="", icon = custom_icon)    


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

    texture_size_type = (
        ('512', "512", ""),
        ('1024', "1024", ""),
        ('2048', "2048", ""),
        ('4096', "4096", ""),
        ('8192', "8192", ""),
    )

    cao_export_location_type = (
        ('0', "Blend", "Store in .blend folder"),
        ('1', "Sub", "Store in subfolder to .blend"),
        #('2', "User", "User specified folder")
    )

    cao_analyze_mode_type = (
        ('Index', "Index", "Detect edges by index"),
        ('Vertex', "Vertex", "Detect edges by vertex position"),
        ('Deep', "Deep", "Detailed edge analysis (heavy)")
    )

    # Export object properties.
    eobj_categories: EnumProperty(
        name="", 
        items=lambda _, __: categories_enum(ASSET_TYPE_OBJECT, empty_too=True),
        description="Export to this category"
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
    eobj_pack_textures: BoolProperty(
        name="Pack Textures to .blend", 
        description="Pack selected textures from materials applied to the exported objects into to .blend file", 
        default=False
        )        
    eobj_rename: EnumProperty(name="Rename", items=export_rename_type, default="2")
    eobj_rename_material: EnumProperty(name="Rename", items=export_rename_type, default="2")
    eobj_export_type: EnumProperty(name="Export", items=export_type)

    eobj_new_categories: EnumProperty(
        name="", 
        items=lambda _, __: categories_enum(ASSET_TYPE_OBJECT, include_root=True, empty_too=True),
        description="Create new subdirectory here"
        )
    eobj_new_category: StringProperty(name="", description="Put new category name in here")

    eobj_pack_textures_list: CollectionProperty(type=TexturesToExport)
    eobj_pack_textures_index: IntProperty(default=0)


    # Import properties.
    iobj_categories: EnumProperty(
        name="", 
        description="Object category",
        items=lambda _, __: categories_enum(ASSET_TYPE_OBJECT),
        update=lambda self, __: self.reset_enum_selection(ASSET_TYPE_OBJECT)
    )
    iobj_previews: EnumProperty(
        items=lambda self, __: PreviewHelper.getDynamicCollection(
            ASSET_TYPE_OBJECT, 
            CollectionImageParser(),
            (ASSET_TYPE_OBJECT, self.iobj_categories)
        ).items
    )
    iobj_at_cursor: BoolProperty(name="At Cursor", description="Move imported objects to cursor position", default=False)
    iobj_lock_xy: BoolProperty(name="Lock XY", description="Lock in XY plane (move & rotation)")
    imat_categories: EnumProperty(
        name="", 
        description="Material category",
        items=lambda _, __: categories_enum(ASSET_TYPE_MATERIAL),
        update=lambda self, __: self.reset_enum_selection(ASSET_TYPE_MATERIAL)
    )
    imat_previews: EnumProperty(
        items=lambda self, __: PreviewHelper.getDynamicCollection(
            ASSET_TYPE_MATERIAL, 
            CollectionImageParser(),
            (ASSET_TYPE_MATERIAL, self.imat_categories)
        ).items
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
        items=lambda _, __: categories_enum(ASSET_TYPE_MATERIAL, empty_too=True),
        description="Export to this category"
    )
    nw_new_category: StringProperty(name="", description="Put new category name in here")
    nw_new_categories: EnumProperty(
        name="", 
        items=lambda _, __: categories_enum(ASSET_TYPE_MATERIAL, include_root=True, empty_too=True),
        description="Create new subdirectory here"
        )


    # Curvature & AO settings.
    cao_export_location: EnumProperty(name="Export location", items=cao_export_location_type, default="1")
    cao_export_subfolder: StringProperty(name="", default="maps", description="Sub folder to .blend")
    cao_export_userfolder: StringProperty(name="", description="Folder for maps")
    cao_export_map_basename: StringProperty(name="", default="mask", description="Map base name (_ao and _curv is appended automatically)")

    cao_uv_map: EnumProperty(
        name="", 
        items=lambda self, context: self.active_uv_maps(context)
    )
    cao_uv_map_distance_auto: BoolProperty(name="Auto Island Distance", default=True)
    cao_uv_map_distance: FloatProperty(name="Island Distance", default=0.01)

    cao_ao_size: EnumProperty(name="AO Size", items=texture_size_type, default="512")
    cao_ao_quality: IntProperty(name="Quality", min=1, max=128, default=16)
    cao_ao_distance: FloatProperty(name="Distance", min=0.001, max=100, default=0.25)
    cao_ao_local: BoolProperty(name="Local only", default=True)
    cao_ao_margin: IntProperty(name="Bake margin", default=16)

    cao_curv_size: EnumProperty(name="Curve Size", items=texture_size_type, default="2048")
    cao_analyze_mode: EnumProperty(name="Analyze Mode", items=cao_analyze_mode_type, default="Vertex")
    cao_curv_min_angle: IntProperty(name="Min Angle", min=0, max=90, default=10)
    cao_curv_line_thickness: IntProperty(name="Line Thickness", min=1, max=128, default=16)
    cao_curv_apply_modifiers: BoolProperty(name="Apply Modifiers", default=False)

    def active_uv_maps(self, context):
        """
        Create enum list for UV layers of currently selected object.
        """
        obj = context.active_object
        layers = []
        if obj:
            for l in obj.data.uv_layers:
                layers.append((l.name, l.name, ""))
        if not layers:
            layers.append(("__DUMMY__", "", ""))
        return layers


    def reset_enum_selection(self, asset_type: str):
        if asset_type == ASSET_TYPE_OBJECT:
            self.iobj_previews = PreviewHelper.getDynamicCollection(
                ASSET_TYPE_OBJECT, 
                CollectionImageParser(),
                (ASSET_TYPE_OBJECT, self.iobj_categories)
            ).items[0][0]
        elif asset_type == ASSET_TYPE_MATERIAL:
            self.imat_previews = PreviewHelper.getDynamicCollection(
                ASSET_TYPE_MATERIAL, 
                CollectionImageParser(),
                (ASSET_TYPE_MATERIAL, self.imat_categories)
            ).items[0][0]


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

