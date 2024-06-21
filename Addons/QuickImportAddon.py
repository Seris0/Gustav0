
#idk lmaooo
#Original Author: LeoToorez/LeoMods edit by Gustav0
#V1.1

import os
import re
import bpy
import io
from glob import glob
from array import array
import struct
import numpy
import itertools
import collections
import os
import textwrap
from blender_dds_addon import import_dds
from bpy.utils import register_class, unregister_class
from bpy.types import Operator, Panel, PropertyGroup
from bpy_extras.io_utils import unpack_list, ImportHelper, ExportHelper, axis_conversion
from bpy.props import BoolProperty, StringProperty, CollectionProperty, PointerProperty
from bpy_extras.image_utils import load_image
from mathutils import Matrix, Vector

bl_info = {
    "name": "Quick GIMI Import",
    "blender": (2, 80, 0),
    "author": "LeoTorreZ / LeoMods edited by Gustav0",
    "location": "File > Import-Export",
    "description": "Eases the import and set up process of GIMI dumps.",
    "category": "Import-Export",
    "tracker_url": "https://github.com/leotorrez/LeoTools",
}


IS_SRMI = True

try:
    from blender_3dmigoto_srmi import Import3DMigotoFrameAnalysis
except ModuleNotFoundError as err1:
    try:
        from blender_3dmigoto_gimi import Import3DMigotoFrameAnalysis
        IS_SRMI = False
    except ModuleNotFoundError as err2:
        from SRMI import Import3DMigotoFrameAnalysis


class QuickImportSettings(bpy.types.PropertyGroup):
    tri_to_quads: BoolProperty(
        name="Tri to Quads",
        default=False,
        description="Enable Tri to Quads"
    )
    merge_by_distance: BoolProperty(
        name="Merge by Distance",
        default=False,
        description="Enable Merge by Distance"
    )
    apply_textures: BoolProperty(
        name="Apply Textures",
        default=True,
        description="Apply Materials and Textures"
    )

class TextureHandler:
    @staticmethod
    def new_material(name, texture_name):
        """Creates a new material using that texture as base color. also sets alpha to none"""
        material = bpy.data.materials.new(name)
        material.use_nodes = True
        bsdf = material.node_tree.nodes["Principled BSDF"]
        bsdf.inputs[0].default_value = (1, 1, 1, 1)
        bsdf.inputs[5].default_value = 0.0
        # add texture
        texImage = material.node_tree.nodes.new("ShaderNodeTexImage")
        # get already imported texture
        texture_name = texture_name[:-4]
        texImage.image = bpy.data.images.get(texture_name)
        texImage.image.alpha_mode = "NONE"
        # link texture to bsdf
        material.node_tree.links.new(texImage.outputs[0], bsdf.inputs[0])
        return material.name

    @staticmethod
    def import_dafile(context, file):
        """Import a file."""
        dds_options = context.scene.dds_options
        tex = import_dds.load_dds(
            file,
            invert_normals=dds_options.invert_normals,
            cubemap_layout=dds_options.cubemap_layout,
        )
        return tex

    @staticmethod
    def import_files(context, files, path):
        importedmeshes = []
        for file in files:
            # Extract mesh name from the file name
            mesh_name = bpy.path.display_name_from_filepath(os.path.join(path, file))
            # remove "Diffuse" from end of name
            mesh_name = mesh_name[:-7]

            # Import the file
            TextureHandler.import_dafile(context, file=os.path.join(path, file))

            if context.scene.quick_import_settings.apply_textures:
                # Create a material for the mesh only if apply_textures is true
                # Assign the material to the imported mesh
                material_name = "mat_" + mesh_name
                mat = TextureHandler.new_material(material_name, file)

                # find first mesh that has mesh_name at the start of their name
                for obj in bpy.data.objects:
                    print(f"Checking {obj.name} against {mesh_name}")
                    if obj.name.startswith(mesh_name):
                        # append created material
                        print(f"FOUND! Assigning material {mat} to {obj.name}")
                        obj.data.materials.append(bpy.data.materials.get(mat))
                        importedmeshes.append(obj)

        return importedmeshes

class QuickImportPanel(Panel):
    bl_label = "Quick Import GIMI/SRMI"
    bl_idname = "PT_QuickImportPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'QuickImport'
 
    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        row.operator("import_scene.3dmigoto_frame_analysis", text="Setup Character", icon='IMPORT')

        # Adiciona um botão para chamar a funcionalidade QuickImport
        row = layout.row()
        row.operator("import_scene.quick_import", text="Import Using Quick Import", icon='IMPORT')

        #  Adiciona caixas de seleção para Tri to Quads e Merge by Distance
        layout.prop(context.scene.quick_import_settings, "tri_to_quads")
        layout.prop(context.scene.quick_import_settings, "merge_by_distance")
        layout.prop(context.scene.quick_import_settings, "apply_textures")

class QuickImport(Import3DMigotoFrameAnalysis):
    bl_idname = "import_scene.3dmigoto_frame_analysis"
    bl_label = "Quick Import for GIMI"
    bl_options = {"UNDO"}

    def execute(self, context):
        super().execute(context)
        folder = os.path.dirname(self.properties.filepath)
        print("------------------------")
        print("------------------------")
        print("------------------------")

        print(f"Found Folder: {folder}")
        # get all the files in the folder ends in diffuse.dds
        files = os.listdir(folder)
        files = [f for f in files if f.endswith("Diffuse.dds")]
        print(f"List of files:{files}")

        # Import files and assign textures if apply_textures is true
        importedmeshes = TextureHandler.import_files(context, files, folder)

        if context.scene.quick_import_settings.tri_to_quads:
            bpy.ops.object.mode_set(mode='EDIT')          
            bpy.ops.mesh.select_all(action='SELECT') 
            bpy.ops.mesh.tris_convert_to_quads(uvs=True,vcols=True,seam=True,sharp=True,materials=True)
            bpy.ops.mesh.delete_loose()
            
        if context.scene.quick_import_settings.merge_by_distance:
            bpy.ops.object.mode_set(mode='EDIT')          
            bpy.ops.mesh.select_all(action='SELECT') 
            bpy.ops.mesh.remove_doubles(use_sharp_edge_from_normals=True)   
            bpy.ops.mesh.delete_loose()
            
        if context.scene.quick_import_settings.apply_textures:
            bpy.ops.object.mode_set(mode='EDIT')          
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.delete_loose()
            
        return {"FINISHED"}
        

def menu_func_import(self,context):
    self.layout.operator(QuickImport.bl_idname, text="Quick Import for GIMI")


def register():
    bpy.utils.register_class(QuickImport)
    bpy.utils.register_class(QuickImportPanel)
    bpy.utils.register_class(QuickImportSettings)
    #bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.Scene.quick_import_settings = PointerProperty(type=QuickImportSettings)

def unregister():
    bpy.utils.unregister_class(QuickImport)
    bpy.utils.unregister_class(QuickImportPanel)
    bpy.utils.unregister_class(QuickImportSettings)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    del bpy.types.Scene.quick_import_settings

if __name__ == "__main__":
    register()