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
from typing                 import List, Tuple

ASSET_TYPE_OBJECT = "objects"
ASSET_TYPE_MATERIAL = "materials"
ASSET_TYPE_HDRI = "hdri"
ASSET_TYPE_NODES = "nodes"
ASSET_TYPE_NODES_MATERIALS = "nodes_materials"

PREVIEW_EXT = ".png"

class AssetFolder:
    def __init__(self, path: str, name: str, depth: int, icon: str = None):
        self.path = path
        self.name = name
        self.depth = depth
        self.asset_number = 0
        self.folders = []


    def add_folder(self, folder):
        self.folders.append(folder)


    def inc_asset_number(self):
        self.asset_number += 1


    def build_name(self) -> str:
        if self.depth > 1:
            return f"{(self.depth - 1) * '.'}/{self.name} ({self.asset_number})"
        else:
            return f"{self.name} ({self.asset_number})"


    def get_entries(self, include_root: bool, empty_too: bool) -> List[Tuple[str, str, str]]:
        r = []
        if self.depth == 0:
            if include_root:
                r.append((self.path, "<ROOT>", self.path))
        else:                
            if empty_too or self.asset_number > 0:
                r.append((self.path, self.build_name(), self.path))

        for af in self.folders:
            r.extend(af.get_entries(include_root, empty_too))

        return r


    def get_name_list(self) -> List[str]:
        r = [ self.build_name(), ]
        for af in self.folders:
            r.extend(af.get_name_list())
        return r


def formats_to_parse(asset_type: str) -> List[str]:
    """
    Return list of extensions to show in previews (.blend, .fbx)
    """
    extensions = []
    if asset_type == ASSET_TYPE_OBJECT:
        preferences = PreferencesPanel.get()
        extensions.clear()
        if preferences.show_blend: extensions.append('.blend')
        if preferences.show_fbx: extensions.append('.fbx')
    elif asset_type == ASSET_TYPE_MATERIAL:
        extensions.append(".blend")

    return tuple(extensions)


class CategoriesCache:
    """
    Caches the different directory structures, so they must not be parsed that often.
    """
    cache = {
        ASSET_TYPE_OBJECT: None,
        ASSET_TYPE_MATERIAL: None
    }

    @staticmethod
    def rec_scan_structure(asset_type, basedir="", depth=0) -> AssetFolder:
        """
        Return categories (e.g. sub-dirs) from given asset_type (objects, materials, ...).
        """
        use_icons = PreferencesPanel.get().use_category_icons
        extensions = formats_to_parse(asset_type)

        path = os.path.join(PreferencesPanel.get().root, asset_type, basedir)
        if os.path.exists(path):
            icon = os.path.join(part, "icon.png") if use_icons else None

            asset_folder = AssetFolder(
                "<ROOT>" if depth == 0 else basedir, 
                "<ROOT>" if depth == 0 else os.path.split(path)[1], 
                depth,
                icon if icon and os.path.exists(icon) else None
            )

            for e in sorted(os.listdir(path)):
                abs_path = os.path.join(path, e)

                if os.path.isdir(abs_path) and not e.startswith('.'):
                    rel_path = os.path.join(basedir, e)
                    # Do this recursively
                    asset_folder.add_folder(CategoriesCache.rec_scan_structure(asset_type, rel_path, depth + 1))

                elif os.path.isfile(abs_path) and e.endswith(extensions):
                    asset_folder.inc_asset_number()

            return asset_folder

        return AssetFolder(path, "<ROOT>", 0)


    @staticmethod 
    def update_cache(asset_type):
        CategoriesCache.cache[asset_type] = CategoriesCache.rec_scan_structure(asset_type)


    @staticmethod
    def categories(asset_type: str):
        if not CategoriesCache.cache[asset_type]:
            CategoriesCache.update_cache(asset_type)
        return CategoriesCache.cache[asset_type].get_name_list()


    @staticmethod
    def categories_enum(asset_type: str, include_root: bool, empty_too: bool):
        if not CategoriesCache.cache[asset_type]:
            CategoriesCache.update_cache(asset_type)
        return CategoriesCache.cache[asset_type].get_entries(include_root, empty_too)



def categories(asset_type):
    return CategoriesCache.categories(asset_type)


def categories_enum(asset_type, include_root = False, empty_too = False):
    return CategoriesCache.categories_enum(asset_type, include_root, empty_too)    


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

    extensions = formats_to_parse(asset_type)

    entries = []
    try:
        for f in os.listdir(path):
            if f.lower().endswith(extensions):
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
    except Exception as ex:
        print(f"Can't parse: {path}")
    
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

   