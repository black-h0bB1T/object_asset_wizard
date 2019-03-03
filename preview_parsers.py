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

from . preferences          import PreferencesPanel
from . utils                import parse_entry_list, split_entry

class CollectionImageParser:
    """
    Parser for PreviewHelper. Parses all supported objects and creates
    the collection using the preview images.
    data = [asset_type, category]
    """
 
    def parse(self, lst):
        """
        Parses the directory for supported files and create list from 
        preview images.
        """
        asset_type, category = lst.data
        fp = os.path.join(PreferencesPanel.get().root, asset_type, category)
        print("Parse collection: ", fp)

        id = 0
        noIcon = os.path.join(os.path.dirname(__file__), "data", "No_Icon.png")
        for entry in parse_entry_list(asset_type, category):
            if not lst.collection: # lazy init
                lst.collection = bpy.utils.previews.new()

            imp, preview, label, mat = split_entry(entry)
            if os.path.exists(preview):
                thumb = lst.collection.load(entry, preview, 'IMAGE')
            else:
                thumb = lst.collection.load(entry, noIcon, 'IMAGE')
            lst.items.append((entry, label, label, thumb.icon_id, id))
            id += 1


class NodesParser:
    """
    Parses nodes from specific blend file, load previews from respective
    data folder.
    data = blend basename/folder name.
    """

    def parse(self, lst):
        """
        Parse node elements.
        """
        id = 0
        data = os.path.join(os.path.dirname(__file__), "data")
        noIcon = os.path.join(data, "No_Icon.png")
        blend = os.path.join(data, lst.data + ".blend")
        previews = os.path.join(data, lst.data)
        with bpy.data.libraries.load(blend, link=False) as (data_src, data_dst):
            for group in data_src.node_groups:
                if group.startswith("NW_"):
                    preview = os.path.join(previews, group + ".png")
                    if not lst.collection: # lazy init
                        lst.collection = bpy.utils.previews.new()
                    if os.path.exists(preview):
                        thumb = lst.collection.load(group, preview, 'IMAGE')
                    else:
                        thumb = lst.collection.load(group, noIcon, 'IMAGE')
                    lst.items.append(("%s::%s" % (blend, group), group, "", thumb.icon_id, id))
                    id += 1
