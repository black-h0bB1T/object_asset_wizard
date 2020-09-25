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
from bpy.props              import BoolProperty

from . preferences          import PreferencesPanel
from . execute_blender      import run_preview_render
from . preview_parsers      import CollectionImageParser
from . utils                import (CategoriesCache, categories, parse_entry_list, split_entry, 
                                        ASSET_TYPE_OBJECT, ASSET_TYPE_MATERIAL)
from . properties           import Properties

running = False

class ModalTimerOperator(Operator):
    """
    Used to track background rendering.
    """
    bl_idname = "asset_wizard.modal_timer_op"
    bl_label = "Modal Timer Operator"

    timer = None

    def modal(self, context, event):
        if event.type == 'TIMER':
            Properties.get_render_previews().poll()

        return {'PASS_THROUGH'}


    def execute(self, context):
        global running

        wm = context.window_manager

        # Do it only once ...
        if not running:
            self.timer = wm.event_timer_add(0.1, window=context.window)
            wm.modal_handler_add(self)
            running = True
            return {'RUNNING_MODAL'}
        else:
            return {'FINISHED'}


    def cancel(self, context):
        context.window_manager.event_timer_remove(self.timer)


class RenderPreviews:
    def __init__(self):
        # (asset_type, full path)
        self.jobs = []

        # subprocess.Popen
        self.process = None 


    def poll(self):
        """
        Check if render process is active. If completed, cleanup.
        Start next if there's one on the pipe.
        """
        if self.process:
            # Job is active. Check if it has completed
            if self.process.poll() != None:
                # It has, reset.
                self.process = None 

                # Refresh view (if preview currently selected).
                if self.jobs[0][0] == ASSET_TYPE_OBJECT:
                    CategoriesCache.update_cache(ASSET_TYPE_OBJECT)
                    if self.jobs[0][1] == Properties.get().iobj_previews:
                        bpy.ops.asset_wizard.refresh_object_previews_op()
                elif self.jobs[0][0] == ASSET_TYPE_MATERIAL:
                    CategoriesCache.update_cache(ASSET_TYPE_MATERIAL)
                    if self.jobs[0][1] == Properties.get().imat_previews:
                        bpy.ops.asset_wizard.refresh_material_previews_op()
                
                self.jobs.pop(0)

                # Force UI redraw (status display).
                if bpy.context.area:
                    bpy.context.area.tag_redraw()

        # If None, we can start a new one.
        if not self.process and self.jobs:
            self.process = run_preview_render(
                self.jobs[0][0],
                self.jobs[0][1],
                PreferencesPanel.get().preview_engine
            )

            # Force UI redraw (status display).
            if bpy.context.area:
                bpy.context.area.tag_redraw()


    def add_job(self, asset_type, filename):
        """
        Add new job for preview rendering.
        """
        # (Eventually) start modal timer.
        bpy.ops.asset_wizard.modal_timer_op()

        self.jobs.append((asset_type, filename))
        self.poll()


    def parse_render_list(self, root, asset_type, rerender):
        """
        Adds all files that need to be preview rendered to job list.
        """
        for category in categories(asset_type):
            for entry in parse_entry_list(asset_type, category):
                if rerender:
                    self.add_job(asset_type, entry)
                else:
                    preview = split_entry(entry)[1]
                    if not os.path.exists(preview):
                        self.add_job(asset_type, entry)


    def generate_render_list(self, rerender):
        """
        Generate full render list in job list.
        """
        prefs = PreferencesPanel.get()
        for asset_type in ( ASSET_TYPE_OBJECT, ASSET_TYPE_MATERIAL ):
            self.parse_render_list(prefs.root, asset_type, rerender)


    def status(self):
        if self.jobs:
            return "Render queue (%i to render)::Current: %s" % (len(self.jobs), os.path.basename(self.jobs[0][1]))
        else:
            return None


class RenderPreviewsOperator(Operator):
    bl_idname = "asset_wizard.render_previews_op"
    bl_label = "Render"
    bl_description = "Render missing previews"

    def execute(self, context):
        Properties.get_render_previews().generate_render_list(False)
        return{'FINISHED'}    


class RenderAllPreviewsOperator(Operator):
    bl_idname = "asset_wizard.render_all_previews_op"
    bl_label = "Render ALL"
    bl_description = "Render ALL previews (can take a *LONG* time!)"

    def execute(self, context):
        Properties.get_render_previews().generate_render_list(True)
        return{'FINISHED'}          

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)      
