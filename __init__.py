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

import bpy, platform, os, stat

from . preferences          import PreferencesPanel
from . properties           import Properties
from . preview_parsers      import CollectionImageParser, NodesParser
from . preview_helper       import PreviewHelper
from . panels               import ImportPanel, ExportPanel, NodeWizardPanel, NodeWizardMapPanel, NodeWizardExportPanel
from . create_category_ops  import CreateCategoryOperator
from . exporter_ops         import UseObjectNameOperator, OverwriteObjectExporterOperator, ObjectExporterOperator
from . importer_ops         import (AppendObjectOperator, LinkObjectOperator, 
                                        SetMaterialOperator, AppendMaterialOperator, OpenObjectOperator, OpenMaterialOperator)
from . render_previews_ops  import ModalTimerOperator, RenderPreviewsOperator, RenderAllPreviewsOperator   
from . generate_ops         import GeneratePBROperator, GenerateImageOperator, ExportPBROperator, ExportMaterialOperator             
from . node_importer_ops    import NodeImporter   
from . ao_curv_calc_ops     import BakeAoMapOperator, CurvatureMapOperator, AoNodeOperator, CurvatureNodeOperator, MapGenerateUV, UseObjectNameForMap
from . tools_ops            import (DX2OGLConverterOperator, GenerateTwoLayerTextureBasedSetupOperator,
                                        GenerateTwoLayerShaderBasedSetupOperator, ImportDistortionOperator,
                                        ImportBlurOperator, ImportTextureBoxMapUVW, ImportExtNoise,
                                        ImportExtMusgrave, ImportExtVoronoi, ImportMixNoise,
                                        ImportScalarMix, ImportIntensityVisualizer, ImportScalarMapper,
                                        ImportNormalDirection, ImportSlice)             
from . support_ops          import RefreshObjectPreviews, ReRenderObjectPreview, RefreshMaterialPreviews, ReRenderMaterialPreview                                        
from . utils                import (categories, ASSET_TYPE_OBJECT, ASSET_TYPE_MATERIAL,
                                        ASSET_TYPE_NODES, ASSET_TYPE_NODES_MATERIALS)

# 0.1.7
#   bl_idname added to panels
# 0.1.6
#   Error fixes:
#   - Create directory if not exists when creating curvature mask
# 0.1.5
#   Error fixes:
#   - Append at cursor (Blender API change)
#   - Wrong library when creating root category
#   - curvature executable flag on Linux
# 0.1.4
#   Append/Add object at cursor position
#   Lock appended object in XY plane (Move in Z and rotation in X/Y axis is locked for these objects)
#   Both object and materials can now have subdirectories
#   Categories are now cached an don't need to be rescanned on every panel redraw
# 0.1.3
#   Curvature and AO map generator added to Node Wizard
#   Preview size in panels can now be scaled from preferences
#   Fix in preferences (use of __package__)
#   Near and far clipping clipping plane of preview camera adjusted to allow smaller and larger objects
# 0.1.2
#   Better view on objects in preview
#   Support for multiple material in one .blend added
#   Update Preview if selected only
#   Open button for materials added
# 0.1.1
#   Package Name Fix (assert -> asset)
# 0.1
#   Initial Release                                        

# +TODO: Automatic name suggestion on obj selection -> use name of active_object
# +TODO: Compact export panel -> compact adjustable in prefs
# +TODO: Integrate Node Wizard with export and generate
# +TODO: Render in background thread
# +TODO: Reload button for previews
# +TODO: Rerender selected assets
# +TODO: Check panel/op validity using poll()/enable
# +TODO: Unify preview object from Asset & Node-Wizard
# +TODO: No-Icon for Asset Wizard
# +TODO: Preview FBX render
# +TODO: NW: Fix utils import + nodes_materials
# +TODO: Finalize better handling of empty repositories
# +TODO: Reload previews automatically after preview-render
# +TODO: Auto render exported things
# +TODO: Better view on objects in preview
# +TODO: Support multiple materials in one .blend
# +TODO: Update Preview if selected only
# +TODO: Open button for materials added
# +TODO: --Release
# +TODO: Preview scale adjustable
# +TODO: Change near and far clipping setting in preview.blend
# +TODO: NW: Quick bake curvature and AO mask
# +TODO: Append object at cursor, optionally lock Move Z & Rotate XY
# +TODO: Sub-categories

# TODO: Fix linux curvature library dependency (GLIBC) bug
# TODO: ?Adjustable rows/columns for previews (possible?)
# TODO: Some default settings (e.g. for exporter) should be adjustable in prefs
# TODO: NW: One click create paint texture for mask
# TODO: NW: Better Masks
# TODO: NW: Finalize different texture unrepeater solutions
# TODO: NW: Finalize procedural wood shader
# TODO: NW?: Finalize moss generator (?metaball using object parser)
# TODO: STL (OpenSCAD), ?OBJ support
# TODO: DOC/VideoTutorial

# TODO: ?Integrate HDRI
# TODO: ?Integrate particles
# TODO: ?Move or delete assets
# TODO: ?Import 3DS/JSON
# TODO: ?Download new masks & materials from cloud/github
# TODO: ?Import GIMP gradients as ColorRamp

bl_info = {
    "name" : "Asset Wizard",
    "version": (0, 1, 7),
    "author" : "h0bB1T",
    "description" : "Asset import and export utility.",
    "blender" : (2, 80, 0),
    "location" : "View3D",
    "category" : "Import-Export"
}

ops = [
    PreferencesPanel,
    Properties,
    ImportPanel,
    ExportPanel,
    NodeWizardPanel,
    NodeWizardMapPanel,
    NodeWizardExportPanel,
    CreateCategoryOperator,
    UseObjectNameOperator,
    OverwriteObjectExporterOperator,
    ObjectExporterOperator,
    AppendObjectOperator, 
    LinkObjectOperator, 
    SetMaterialOperator, 
    AppendMaterialOperator, 
    OpenObjectOperator,
    OpenMaterialOperator,
    ModalTimerOperator,
    RenderPreviewsOperator,
    RenderAllPreviewsOperator,
    GeneratePBROperator, 
    GenerateImageOperator, 
    ExportPBROperator,
    ExportMaterialOperator,
    NodeImporter,
    BakeAoMapOperator,
    CurvatureMapOperator,
    AoNodeOperator,
    CurvatureNodeOperator,
    UseObjectNameForMap,
    MapGenerateUV,
    DX2OGLConverterOperator, 
    GenerateTwoLayerTextureBasedSetupOperator,
    GenerateTwoLayerShaderBasedSetupOperator, 
    ImportDistortionOperator,
    ImportBlurOperator, 
    ImportTextureBoxMapUVW, 
    ImportExtNoise,
    ImportExtMusgrave, 
    ImportExtVoronoi, 
    ImportMixNoise,
    ImportScalarMix, 
    ImportIntensityVisualizer, 
    ImportScalarMapper,
    ImportNormalDirection, 
    ImportSlice,
    RefreshObjectPreviews,
    ReRenderObjectPreview,
    RefreshMaterialPreviews,
    ReRenderMaterialPreview,
]

def register():
    for op in ops:
        bpy.utils.register_class(op)

    # Prepare previews for importer
    for asset_type in (ASSET_TYPE_OBJECT, ASSET_TYPE_MATERIAL):
        dirs = categories(asset_type)
        PreviewHelper.addCollection(
            asset_type,
            CollectionImageParser(), 
            (asset_type, dirs[0] if dirs else "")
        )

    # Prepare previews for node wizard
    for (asset_type, mod) in (
        (ASSET_TYPE_NODES, "nodes"),
        (ASSET_TYPE_NODES_MATERIALS, "materials")
        ):
        PreviewHelper.addCollection(asset_type, NodesParser(), mod)        

    Properties.initialize()

    # On Linux, guarantee curvature has execute rights.
    if platform.system() == "Linux":
        os.chmod(
            os.path.join(os.path.dirname(__file__), "data", "tools", "curvature"),
            stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH |
            stat.S_IWUSR | stat.S_IWGRP |
            stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        )

def unregister():
    Properties.cleanup()

    PreviewHelper.removeAllCollections()

    for op in ops:
        bpy.utils.unregister_class(op)

if __name__ == "__main__":
    register()    
