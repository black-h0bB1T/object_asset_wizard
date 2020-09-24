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

import bpy, subprocess, os

from . utils                import split_entry

# From asset-flinger
# https://stackoverflow.com/questions/4417546/constantly-print-subprocess-output-while-process-is-running
def execute_silent(cmd):
    """
    Runs an external application, in this case the blender executable for
    thumbnail generation. Returns all lines written by this application to stdout
    immediately on a line by line basis.
    """
    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line
    popen.stdout.close()
    _ = popen.wait()
    #if return_code:
    #    raise subprocess.CalledProcessError(return_code, cmd)

def execute(cmd):
    """
    Runs an external application, in this case the blender executable for
    thumbnail generation. 
    Returns the object to watch for completion.
    """
    return subprocess.Popen(cmd, universal_newlines=True)

def execute_blender(args):
    """
    Execute Blender with given arguments.
    Returns the object to watch for completion.
    """
    args.insert(0, bpy.app.binary_path)
    print(" ".join(args))
    return execute(args)

# blender --background --factory-startup --python fix_blend.py -- [Asset.blend] --pack X.png --pack Y.png ..
def run_blend_fix(asset, pack):
    """
    Fixes the given .blend file, by instancing all objects in the active scene.
    """
    args = [
        "--background",
        "--factory-startup",
        "--python",
        os.path.join(os.path.dirname(__file__), "fix_blend.py"),
        "--",
        asset,
    ]

    for p in pack:
        args.append("--pack")
        args.append(p)
    
    execute_blender(args).wait() # Wait for completion.

def run_preview_render(asset_type, filename, engine):
    """
    Render a preview for the given .blend file.
    Returns the object to watch for completion.
    """
    args = [
        "--background",
        "--factory-startup",
        os.path.join(os.path.dirname(__file__), "data", "preview.blend"),
        "--python",
        os.path.join(os.path.dirname(__file__), "render_script.py"),
        "--",
        filename,
        split_entry(filename)[1],
        asset_type,
        engine
    ]
    
    return execute_blender(args)
