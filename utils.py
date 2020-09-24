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
from . icon_helper          import IconHelper
from typing                 import List

ASSET_TYPE_OBJECT = "objects"
ASSET_TYPE_MATERIAL = "materials"
ASSET_TYPE_HDRI = "hdri"
ASSET_TYPE_NODES = "nodes"
ASSET_TYPE_NODES_MATERIALS = "nodes_materials"

PREVIEW_EXT = ".png"
FORMATS = (".blend", ".fbx")

class CategoriesCache:
    """
    Caches the different directory structures, so they must not be parsed that often.
    """
    cache = {
        ASSET_TYPE_OBJECT: [],
        ASSET_TYPE_MATERIAL: []
    }

    @staticmethod
    def rec_scan_structure(asset_type, basedir=""):
        """
        Return categories (e.g. sub-dirs) from given asset_type (objects, materials, ...).
        """
        path = os.path.join(PreferencesPanel.get().root, asset_type, basedir)
        use_icons = PreferencesPanel.get().use_category_icons
        cats = []
        if os.path.exists(path):
            for e in sorted(os.listdir(path)):
                p = os.path.join(path, e)
                if os.path.isdir(p) and not e.startswith('.'):
                    if use_icons:
                        icon = os.path.join(p, "icon.png")
                        cats.append((os.path.join(basedir, e), icon if os.path.exists(icon) else None))
                    else:
                        cats.append((os.path.join(basedir, e), None))
                if os.path.isdir(p):
                    cats += (CategoriesCache.rec_scan_structure(asset_type, os.path.join(basedir, e)))
        return cats


    @staticmethod 
    def update_cache(asset_type):
        CategoriesCache.cache[asset_type] = CategoriesCache.rec_scan_structure(asset_type)


    @staticmethod
    def categories(asset_type):
        if not CategoriesCache.cache[asset_type]:
            CategoriesCache.update_cache(asset_type)
        return CategoriesCache.cache[asset_type]


def categories(asset_type):
    return CategoriesCache.categories(asset_type)


def list_to_enum(lst, include_root=False):
    """
    Convert a list of strings to a EnumProperty list (s, s, '', #).
    """
    r = [ ("<ROOT>", "<ROOT>", '', 0) ] if include_root else []
    for item, icon in lst:
        if icon:
            icon_id = IconHelper.get_icon(icon)
            r.append((item, item, '', icon_id, len(r)))
        else:
            r.append((item, item, '', len(r)))
    return r


def export_file(asset_type, category, name, ext):
    """
    Return path to file as specified by the individual name parts.
    """
    return os.path.join(
        PreferencesPanel.get().root, 
        asset_type, 
        category, 
        bpy.path.clean_name(name) + ext
    )


def export_file_exists(asset_type, category, name, ext):    
    """
    Check if file with specified individual name parts exists.
    """
    return os.path.exists(export_file(asset_type, category, name, ext))


def parse_entry_list(asset_type, category):
    """
    Parses the given directory for all supported entries.
    In case of materials, parse .blend if it contains more
    than one material and create multiple entries (path/abc.blend::Material).
    """
    path = os.path.join(
        PreferencesPanel.get().root, 
        asset_type, 
        category
    )

    entries = []
    for f in os.listdir(path):
        if f.lower().endswith(FORMATS):
            fullname = os.path.join(path, f)
            if asset_type == ASSET_TYPE_MATERIAL:
                # Check if there are more than one material in this file.
                with bpy.data.libraries.load(fullname, link=False) as (data_from, data_to):
                    if len(data_from.materials) > 1:
                        for mat in data_from.materials:
                            entries.append(fullname + "::" + mat)
                    else:
                        # Single material file.
                        entries.append(fullname)
            else:
                # Object file
                entries.append(fullname)
    
    return entries


def split_entry(entry_name):
    """
    Splits the given entry in [(blend/fbx), preview, label, material]
    material is "" if not set.
    """
    if "::" in entry_name:
        imp, mat = entry_name.split("::")
        preview = os.path.splitext(imp)[0] + "__" + bpy.path.clean_name(mat) + ".png"
        label = os.path.splitext(os.path.split(imp)[1])[0] + ":" + mat
    else:
        imp, mat = entry_name, ""
        preview = os.path.splitext(imp)[0] + ".png"
        label = os.path.splitext(os.path.split(imp)[1])[0]

    return (imp, preview, label, mat)


def blender_2_8x():
    """
    Check if blender 2.8x is used.
    """
    return bpy.app.version < (2, 90, 0)


def textures_of_node_tree(nt: bpy.types.NodeTree):
    """
    Helper fpr textures_of_object(s).
    """
    r = []
    for n in nt.nodes:
        if n.bl_idname == 'ShaderNodeTexImage':
            if n.image and n.image.filepath:
                r.append(bpy.path.abspath(n.image.filepath))
        elif n.bl_idname == 'ShaderNodeGroup' and n.node_tree:
            r.extend(textures_of_node_tree(n.node_tree))
    return r


def textures_of_object(obj: bpy.types.Object):
    """
    Helper fpr textures_of_objects.
    """
    r = []
    for ms in obj.material_slots:
        if ms.material and ms.material.node_tree:
            r.extend(textures_of_node_tree(ms.material.node_tree))
    return r


def textures_of_objects(objects: List[bpy.types.Object]):
    """
    Get all image textures used by all materials from all objects as set.
    """
    r = []
    for o in objects:
        r.extend(textures_of_object(o))
    return set(r)

   