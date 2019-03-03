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

import os

from bpy.props              import StringProperty
from bpy.types              import Operator

from . preferences          import PreferencesPanel
from . properties           import Properties
from . utils                import ASSET_TYPE_OBJECT, ASSET_TYPE_MATERIAL

class CreateCategoryOperator(Operator):
    bl_idname = "asset_wizard.create_category_op"
    bl_label = "Create New"
    bl_description = "Create new category"
    bl_options = {'REGISTER', 'INTERNAL'}

    asset_type: StringProperty()
    category: StringProperty()

    def execute(self, context):
        path = os.path.join(PreferencesPanel.get().root, self.asset_type, self.category)
        if not os.path.exists(path):
            os.makedirs(path)
            self.report({'INFO'}, "Category created.")

            if self.asset_type == ASSET_TYPE_OBJECT:
                Properties.get().iobj_categories = self.category
                Properties.get().eobj_categories = self.category
            if self.asset_type == ASSET_TYPE_MATERIAL:
                Properties.get().imat_categories = self.category
                Properties.get().nw_categories = self.category

        return {'FINISHED'}
