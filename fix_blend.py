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

# blender --background --factory-startup --python fix_blend.py -- [Asset.blend] [Pack=True/False]
import bpy, sys, argparse

def main(args):
    print("Script args: ", args)

    if len(args) > 0:
        parser = argparse.ArgumentParser()
        parser.add_argument('blend')
        parser.add_argument('--pack', action='append')
        args = parser.parse_args(args)

        blend = args.blend
        packImages = args.pack

        print(f"Blend to fix: {blend}")
        print(f"Images to pack: {packImages}")

        bpy.ops.wm.open_mainfile(filepath=blend)

        for o in bpy.data.objects:
            bpy.context.scene.collection.objects.link(o)
        if packImages:
            for p in packImages:
                for i in bpy.data.images:
                    if i.filepath.endswith(p):
                        i.pack()
                        break
        
        bpy.context.view_layer.update()
        bpy.context.preferences.filepaths.save_version = 0 # No backup blends needed
        bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)

if __name__ == "__main__":
    if "--" not in sys.argv:
        argv = []  # as if no args are passed
    else:
        argv = sys.argv[sys.argv.index("--") + 1:]  # get all args after "--"
    main(argv)
    