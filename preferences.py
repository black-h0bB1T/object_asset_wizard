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

from bpy.types import AddonPreferences
from bpy.props import StringProperty, EnumProperty, BoolProperty, FloatProperty

class PreferencesPanel(AddonPreferences):
    bl_idname = __package__

    preview_engine_type = (
        ('CYCLES', "Cycles", ""),
        ('BLENDER_EEVEE', "Eevee", ""), 
    )

    root: StringProperty(
        name="Asset root directory",
        default="C:/tmp/new_assets", # REMOVE->DEVELOPMENT
        #default=os.path.splitdrive(__file__)[0],
        description="Path to Root Asset Directory",
        subtype="DIR_PATH"
        )

    preview_engine: EnumProperty(name="Preview render engine", items=preview_engine_type)

    compact_panels: BoolProperty(name="Use compact panels", default=True)

    preview_scale: FloatProperty(
        name="Scale factor for previews", 
        default=1.0,
        soft_min=0.2,
        soft_max=5.0
        )

    def draw(self, context):
        self.layout.row().prop(self, "root", text="Root Asset Directory")
        self.layout.row().prop(self, "preview_engine")
        self.layout.row().prop(self, "preview_scale")
        self.layout.row().prop(self, "compact_panels")

    @staticmethod
    def get():
        return bpy.context.preferences.addons[__package__].preferences
