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
from bpy.props              import StringProperty

from . node_utils           import NodeUtils

class NodeImporter(Operator, NodeUtils):
    bl_idname = "asset_wizard.node_importer_op"
    bl_label = "Import node setups"
    bl_description = "Import nodes from supplied node groups and instance them"
    bl_options = {'REGISTER', 'UNDO'}

    # Parameter to select blendFile::NodeGroup.
    group: StringProperty(name="Group")

    @staticmethod
    def import_utils_group(name):
        bpy.ops.asset_wizard.node_importer_op(
            group="%s::%s" % (os.path.join(os.path.dirname(__file__), "data", "utils.blend"), name))

    def import_group(self, blend, group, link):
        """
        Import specfied node group if not already existing. Return true
        if already exists or successfuly imported.
        """
        # Check if already exists ..
        if bpy.data.node_groups.find(group) > -1:
            return True

        # No, try to import ..
        with bpy.data.libraries.load(blend, link=link) as (data_src, data_dst):
            if group not in data_src.node_groups:
                return False # Not available

            data_dst.node_groups = [group]

        return True

    def execute(self, context):
        blend, group = self.group.split("::")
        
        # Make group available ..
        if not self.import_group(blend, group, False):
            self.report({"ERROR"}, "Can't import node group.")
            return{'CANCELLED'}

        # Instanciate group ..
        bpy.ops.node.add_node(
            type="ShaderNodeGroup", 
            use_transform=True, 
            settings=[{
                "name": "node_tree", 
                "value": "bpy.data.node_groups['%s']" % group
                }]
        )
        return bpy.ops.node.translate_attach_remove_on_cancel('INVOKE_DEFAULT')