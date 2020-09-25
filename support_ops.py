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

import bpy

from bpy.types              import Operator

from . properties           import Properties
from . preview_helper       import PreviewHelper
from . utils                import export_file, CategoriesCache, ASSET_TYPE_OBJECT, ASSET_TYPE_MATERIAL

class RefreshObjectPreviews(Operator):
    bl_idname = "asset_wizard.refresh_object_previews_op"
    bl_label = "Refresh"
    bl_description = "Refresh previews for this category (if e.g. externally modified)"

    def execute(self, context):
        PreviewHelper.setData(
            ASSET_TYPE_OBJECT, 
            (ASSET_TYPE_OBJECT, Properties.get().iobj_categories),
            True
        )
        CategoriesCache.update_cache(ASSET_TYPE_OBJECT)
        return {'FINISHED'}


class ReRenderObjectPreview(Operator):
    bl_idname = "asset_wizard.rerender_object_preview_op"
    bl_label = "ReRender"
    bl_description = "ReRender preview for current selection"

    def execute(self, context):
        Properties.get_render_previews().add_job(
            ASSET_TYPE_OBJECT, 
            Properties.get().iobj_previews
        )
        return {'FINISHED'}        


class RefreshMaterialPreviews(Operator):
    bl_idname = "asset_wizard.refresh_material_previews_op"
    bl_label = "Refresh"
    bl_description = "Refresh previews for this category (if e.g. externally modified)"

    def execute(self, context):
        PreviewHelper.setData(
            ASSET_TYPE_MATERIAL, 
            (ASSET_TYPE_MATERIAL, Properties.get().imat_categories),
            True
        )
        CategoriesCache.update_cache(ASSET_TYPE_MATERIAL)
        return {'FINISHED'}        


class ReRenderMaterialPreview(Operator):
    bl_idname = "asset_wizard.rerender_material_preview_op"
    bl_label = "ReRender"
    bl_description = "ReRender preview for current selection"

    def execute(self, context):
        Properties.get_render_previews().add_job(
            ASSET_TYPE_MATERIAL, 
            Properties.get().imat_previews
        )
        return {'FINISHED'}        
