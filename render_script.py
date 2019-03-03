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

import bpy, sys, os

sys.path.append(os.path.dirname(__file__))

#from common_utils           import calc_bounding_box

class PreviewRenderer:
    def __init__(self, inFile, outFile, asset_type, engine):
        self.inFile = inFile
        self.outFile = outFile
        self.asset_type = asset_type
        self.engine = engine


    # def calc_center_and_scale(self, objects):
    #     """
    #     Return center and max(x,y,z) extend of given objects
    #     """
    #     bmin, bmax = calc_bounding_box(objects)
    #     dim = ((bmax[0]-bmin[0]), (bmax[1]-bmin[1]), (bmax[2]-bmin[2]))
    #     center = (dim[0]/2 + bmin[0], dim[1]/2 + bmin[1], dim[2]/2 + bmin[2])
    #     return (center, max(dim))


    def prepare_material_scene(self):
        if "::" in self.inFile:
            filename, material = self.inFile.split("::")
        else:
            filename, material = self.inFile, ""

        # Load all materials from inFile
        with bpy.data.libraries.load(filename, link=False) as (data_from, data_to):
            data_to.materials = data_from.materials
            mats = data_to.materials

        # Set material to first imported one (if at least 1).
        if material == "":
            if len(mats) > 0:
                bpy.data.objects["Preview"].material_slots[0].material = mats[0]
        else:
            bpy.data.objects["Preview"].material_slots[0].material = [
                m for m in mats if m.name == material ][0]


    def prepare_object_scene(self):
        # Remove material preview object.
        bpy.data.objects.remove(bpy.data.objects["Preview"])

        # Deselect all objects.
        [ o.select_set(False) for o in bpy.context.scene.objects ]
        
        if self.inFile.endswith(".blend"):
            # Load all objects from inFile
            with bpy.data.libraries.load(self.inFile, link=False) as (data_from, data_to):
                data_to.objects = data_from.objects
                links = data_to.objects

            # Append all objects to it.
            coll = bpy.context.collection
            for l in links:
                coll.objects.link(l)

            # Select imported objects.
            [ o.select_set(True) for o in links ]
        else:
            # Import objects.  
            bpy.ops.import_scene.fbx(filepath=self.inFile)

        # Move camera, so objects are optimal in view. 
        bpy.ops.view3d.camera_to_view_selected()


    def prepare_and_render(self):
        if self.asset_type == "materials":
            self.prepare_material_scene()
        else: # "objects"
            self.prepare_object_scene()

        bpy.context.scene.render.engine = self.engine
        bpy.context.scene.render.filepath= self.outFile
        bpy.ops.render.render(write_still=True)


def main(args):
    print("Script args: ", args)
    inFile, outFile, asset_type, engine = args
    PreviewRenderer(inFile, outFile, asset_type, engine).prepare_and_render()


if __name__ == "__main__":
    if "--" not in sys.argv:
        argv = []  # as if no args are passed
    else:
        argv = sys.argv[sys.argv.index("--") + 1:]  # get all args after "--"
    main(argv)
