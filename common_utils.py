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

from mathutils              import Vector

def calc_bounding_box(objects):
    """
    Calculate total bounding box for all selected objects.
    """
    mins, maxs = [], []
    for o in objects:
        # https://blender.stackexchange.com/questions/8459/get-blender-x-y-z-and-bounding-box-with-script
        # https://blender.stackexchange.com/questions/129473/typeerror-element-wise-multiplication-not-supported-between-matrix-and-vect
        bbox = [ o.matrix_world @ Vector(corner) for corner in o.bound_box ]
        mins.append((
            min([ v[0] for v in bbox ]),
            min([ v[1] for v in bbox ]),
            min([ v[2] for v in bbox ])
        ))
        maxs.append((
            max([ v[0] for v in bbox ]),
            max([ v[1] for v in bbox ]),
            max([ v[2] for v in bbox ])
        ))

    bmin = (
        min([ b[0] for b in mins ]),
        min([ b[1] for b in mins ]),
        min([ b[2] for b in mins ])
    )
    bmax = (
        max([ b[0] for b in maxs ]),
        max([ b[1] for b in maxs ]),
        max([ b[2] for b in maxs ])
    )

    return (bmin, bmax)
    