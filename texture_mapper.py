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

import os, re

diffuse_ext = "basecolor,base_color,diffuse,diff,albedo,color,col".split(",")
spec_ext = "specular,spec,spc".split(",")
rough_ext = "roughness,rough,rgh".split(",")
gloss_ext = "gloss,gls".split(",")
normal_ext = "normal,norm,nor,nrm".split(",")
metal_ext = "metallic,metal,met".split(",")
height_ext = "height,hgt".split(",")
other_ext = "ao".split(",")
valid_suffixes = "_1k|_2k|_4k|_8k"

def build_reg(name):
    return "(.*)%s(%s)?$" % (name, valid_suffixes)


def matches_type(name, exts):
    """
    Check if name ends with any of the exts given.
    """
    name = name.lower()
    for e in exts:
        if re.match(build_reg(e), name):
            return True
    return False


def find_base_images(path):
    """
    Find diffuse, albedo, basecolor .. images in directory.
    """
    images = []

    for f in os.listdir(path):
        fullName = os.path.join(path, f)
        name = os.path.split(f)[1]
        baseName = os.path.splitext(name)[0]

        for e in diffuse_ext:
            if re.match(build_reg(e), baseName.lower()):
                images.append((fullName, baseName))
                break

    return images


class TextureMapper:
    """
    Automatically map different types of textures based on the ending of the core file name.
    /path/to/file/xxxEXT.jpg/png
    """

    def parse_textures(self, path, baseName):
        """
        Find textures that match the basename prefix and map based on the extension.
        """
        # print("Parse '%s' for '%s'" % (path, baseName))
        self.baseName = baseName.strip("_")
        for f in os.listdir(path):
            fullName = os.path.join(path, f)
            name = os.path.split(f)[1]
            if name.startswith(baseName):
                bName = os.path.splitext(name)[0]
                if (matches_type(bName, diffuse_ext)):
                    self.diffuse = fullName
                elif (matches_type(bName, spec_ext)):
                    self.specular = fullName
                elif (matches_type(bName, rough_ext)):
                    self.roughness = fullName
                elif (matches_type(bName, gloss_ext)):
                    self.gloss = fullName
                elif (matches_type(bName, normal_ext)):
                    self.normal = fullName
                elif (matches_type(bName, metal_ext)):
                    self.metal = fullName
                elif (matches_type(bName, height_ext)):
                    self.height = fullName

        self.valid = self.diffuse != None


    def __init__(self, image):
        """
        CTor, create mapping from any selected texture (independent to ext).
        """
        # Default values.
        self.valid = False
        self.diffuse = self.specular = self.roughness = self.gloss = self.normal = self.metal = self.height = None

        # Prepare search.
        path, name = os.path.split(image)
        baseName = os.path.splitext(name)[0]
        allExt = diffuse_ext + spec_ext + rough_ext + gloss_ext + normal_ext + metal_ext + height_ext + other_ext

        # Check if selected texture matches at least any of the valid extensions.
        for ext in allExt:
            match = re.match(build_reg(ext), baseName.lower())
            if match: 
                self.parse_textures(path, baseName[0:len(match.group(1))])
                break
                