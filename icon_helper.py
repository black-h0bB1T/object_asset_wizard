# Copyright (C) 2019 h0bB1T
#

import bpy

class IconHelper:

    icons = None

    @staticmethod
    def init():
        IconHelper.icons = bpy.utils.previews.new()

    
    @staticmethod
    def dispose():
        bpy.utils.previews.remove(IconHelper.icons)


    @staticmethod
    def get_icon(path: str):
        if path not in IconHelper.icons:
            IconHelper.icons.load(path, path, 'IMAGE')
        return IconHelper.icons[path].icon_id

        