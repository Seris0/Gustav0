
#Author: Gustav0, LeoTorreZ
#Special thanks to Silent for providing several scripts and 3dframeanalyse, and LeoTools for QuickImport.




import os
import bpy
from bpy.props import PointerProperty, StringProperty, EnumProperty, BoolProperty
from bpy.types import Object, Operator, Panel, PropertyGroup
import numpy as np
import re
import importlib
 
if bpy.app.version < (4, 2, 0):
    from blender_dds_addon import import_dds

current_directory = os.path.dirname(os.path.realpath(__file__))
pattern = r'XXMI[-_]?Tools'
matching_directory = None
for root, dirs, files in os.walk(current_directory):
    for directory in dirs:
        if re.search(pattern, directory, re.IGNORECASE):
            matching_directory = os.path.join(root, directory)
            break
    if matching_directory:
        break

if matching_directory is None:
    raise ImportError("No Module.")

relative_path = os.path.relpath(matching_directory, current_directory)
module_name = relative_path.replace(os.path.sep, '.').replace('.py', '') + ".migoto.operators"
try:
    module = importlib.import_module(module_name)
    Import3DMigotoFrameAnalysis = getattr(module, 'Import3DMigotoFrameAnalysis')
except ImportError as e:
    print(f"Error Import module: {e}")
except AttributeError as e:
    print(f"Error'Import3DMigotoFrameAnalysis': {e}")

bl_info = {
    "name": "XXMI Scripts & Quick Import",
    "author": "Gustav0, LeoTorreZ",
    "version": (2, 0),
    "blender": (3, 6, 2),
    "description": "Script Compilation",
    "category": "Object",
    "tracker_url": "https://github.com/Seris0/Gustav0/tree/main/Addons/QuickImportXXMI",
}


class GIMI_TOOLS_PT_main_panel(bpy.types.Panel):
    bl_label = "XXMI Tools"
    bl_idname = "GIMI_TOOLS_PT_MainPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'XXMI Scripts'

    def draw(self, context):
        layout = self.layout

       
        box = layout.box()
        box.prop(context.scene, "show_vertex", icon="TRIA_DOWN" if context.scene.show_vertex else "TRIA_RIGHT", emboss=False, text="Main Tools")
        if context.scene.show_vertex:
         
            box.label(text="Vertex Groups", icon='GROUP_VERTEX')
            row = box.row()
            row.prop(context.scene, "Largest_VG", text="Largest VG")
            row = box.row()
            row.operator("GIMI_TOOLS.fill_vgs", text="Fill Vertex Groups", icon='ADD')
            row = box.row()
            row.operator("GIMI_TOOLS.remove_unused_vgs", text="Remove Unused VG's", icon='X')
            row = box.row()
            row.operator("GIMI_TOOLS.remove_all_vgs", text="Remove All VG's", icon='CANCEL')
            row = box.row()
            row.operator("object.separate_by_material_and_rename", text="Separate by Material", icon='MATERIAL')
            row = box.row()

            # Vertex Group Merge Section
            layout.prop(context.scene, "merge_mode", text="Merge Mode")
            if context.scene.merge_mode == 'MODE1':
                layout.prop(context.scene, "vertex_groups", text="Vertex Groups")
            elif context.scene.merge_mode == 'MODE2':
                layout.prop(context.scene, "smallest_group_number", text="Smallest Group")
                layout.prop(context.scene, "largest_group_number", text="Largest Group")
            layout.operator("object.merge_vertex_groups", text="Merge Vertex")
        
    
        box = layout.box()
        box.prop(context.scene, "show_remap", icon="TRIA_DOWN" if context.scene.show_remap else "TRIA_RIGHT", emboss=False, text="Vertex Group REMAP")
        if context.scene.show_remap:
            box.label(text="Vertex Group REMAP", icon='FILE_REFRESH')  
            row = box.row()
            row.prop_search(context.scene, "vgm_source_object", bpy.data, "objects", text="Source")
            row = box.row()
            row.prop_search(context.scene, "vgm_destination_object", bpy.data, "objects", text="Target")
            row = box.row()
            row.operator("object.vertex_group_remap", text="Run Remap", icon='FILE_REFRESH')  

        # Collapsible Transfer Properties Section
        box = layout.box()
        box.prop(context.scene, "show_transfer", icon="TRIA_DOWN" if context.scene.show_transfer else "TRIA_RIGHT", emboss=False, text="Transfer Properties")
        if context.scene.show_transfer:
            box.label(text="Transfer Properties", icon='OUTLINER_OB_GROUP_INSTANCE')  
            row = box.row()
            row.prop(context.scene, "transfer_mode", text="Transfer Mode")
            if context.scene.transfer_mode == 'COLLECTION':
                row = box.row()
                row.prop_search(context.scene, "base_collection", bpy.data, "collections", text="Original Properties:")
                row = box.row()
                row.prop_search(context.scene, "target_collection", bpy.data, "collections", text="Missing Properties:")
            else:
                row = box.row()
                row.prop_search(context.scene, "base_objectproperties", bpy.data, "objects", text="Original Mesh:")
                row = box.row()
                row.prop_search(context.scene, "target_objectproperties", bpy.data, "objects", text="Modded Mesh:")
            row = box.row()
            row.operator("object.transfer_properties", text="Transfer Properties", icon='OUTLINER_OB_GROUP_INSTANCE')  



class OBJECT_OT_transfer_properties(bpy.types.Operator):
    bl_idname = "object.transfer_properties"
    bl_label = "Transfer Properties"
    bl_description = "Transfer custom properties and transformation data (location, rotation, scale) from one object to another or between collections."

    def execute(self, context):
        mode = context.scene.transfer_mode

        if mode == 'COLLECTION':
            base_collection = context.scene.base_collection
            target_collection = context.scene.target_collection

            if not base_collection or not target_collection:
                self.report({'ERROR'}, 
                    "Invalid Collection(s) selected.\n"
                    "Please make sure you have selected valid collections for both 'Original Properties' and 'Missing Properties' in the panel.")
                return {'CANCELLED'}

            base_prefix_dict = {}
            for base_obj in base_collection.objects:
                prefix = base_obj.name.split("-")[0]
                base_prefix_dict[prefix] = base_obj

            for target_obj in target_collection.objects:
                target_prefix = target_obj.name.split("-")[0]
                if target_prefix in base_prefix_dict:
                    base_obj = base_prefix_dict[target_prefix]


                    for key in list(target_obj.keys()):
                        if key not in '_RNA_UI':  
                            del target_obj[key]


                    for key in base_obj.keys():
                        target_obj[key] = base_obj[key]
                    target_obj.location = base_obj.location
                    target_obj.rotation_euler = base_obj.rotation_euler
                    target_obj.scale = base_obj.scale  


                    log_message = (
                        f"Transferred properties from '{base_obj.name}' to '{target_obj.name}':\n"
                        f"  Location: {target_obj.location}\n"
                        f"  Rotation: {target_obj.rotation_euler}\n"
                        f"  Scale: {target_obj.scale}"
                    )
                    print(log_message)
                    self.report({'INFO'}, log_message)

            self.report({'INFO'}, "Transfer completed for matching objects in the collections.")

        else:
            base_obj = context.scene.base_objectproperties
            target_obj = context.scene.target_objectproperties

            if not base_obj or not target_obj:
                self.report({'ERROR'}, 
                    "Invalid Mesh(es) selected.\n"
                    "Please ensure you have selected valid objects for both 'Original Mesh' and 'Modded Mesh' in the panel.")
                return {'CANCELLED'}

            for key in list(target_obj.keys()):
                if key not in '_RNA_UI': 
                    del target_obj[key]

            for key in base_obj.keys():
                target_obj[key] = base_obj[key]

            target_obj.location = base_obj.location
            target_obj.rotation_euler = base_obj.rotation_euler
            target_obj.scale = base_obj.scale  

            log_message = (
                f"Transferred properties from '{base_obj.name}' to '{target_obj.name}':\n"
                f"  Location: {target_obj.location}\n"
                f"  Rotation: {target_obj.rotation_euler}\n"
                f"  Scale: {target_obj.scale}"
            )
            print(log_message)
            self.report({'INFO'}, log_message)

        return {'FINISHED'}
             
# MARK: MERGE VGS
class OBJECT_OT_merge_vertex_groups(bpy.types.Operator):
    bl_idname = "object.merge_vertex_groups"
    bl_label = "Merge Vertex Groups"
    bl_description = "Merge the VG's based on the selected mode"

    def execute(self, context):
        mode = context.scene.merge_mode
        vertex_groups = context.scene.vertex_groups
        smallest_group_number = context.scene.smallest_group_number
        largest_group_number = context.scene.largest_group_number

        selected_obj = [obj for obj in bpy.context.selected_objects]
        vgroup_names = []

        if mode == 'MODE1':
            vgroup_names = [vg.strip() for vg in vertex_groups.split(",")]
        elif mode == 'MODE2':
            vgroup_names = [str(i) for i in range(smallest_group_number, largest_group_number + 1)]
        elif mode == 'MODE3':
            vgroup_names = list(set(x.name.split(".")[0] for y in selected_obj for x in y.vertex_groups))
        else:
            self.report({'ERROR'}, "Mode not recognized, exiting")
            return {'CANCELLED'}

        if not vgroup_names:
            self.report({'ERROR'}, "No vertex groups found, please double check an object is selected and required data has been entered")
            return {'CANCELLED'}

        for cur_obj in selected_obj:
            for vname in vgroup_names:
                relevant = [x.name for x in cur_obj.vertex_groups if x.name.split(".")[0] == vname]

                if relevant:
                    vgroup = cur_obj.vertex_groups.new(name=f"x{vname}")

                    for vert_id, vert in enumerate(cur_obj.data.vertices):
                        available_groups = [v_group_elem.group for v_group_elem in vert.groups]

                        combined = 0
                        for vg_name in relevant:
                            vg_index = cur_obj.vertex_groups[vg_name].index
                            if vg_index in available_groups:
                                combined += cur_obj.vertex_groups[vg_name].weight(vert_id)

                        if combined > 0:
                            vgroup.add([vert_id], combined, 'ADD')

                    for vg_name in relevant:
                        cur_obj.vertex_groups.remove(cur_obj.vertex_groups[vg_name])
                    vgroup.name = vname

            bpy.context.view_layer.objects.active = cur_obj
            bpy.ops.object.vertex_group_sort()

        return {'FINISHED'}

class GIMI_TOOLS_OT_remove_all_vgs(bpy.types.Operator):
    bl_label = "Remove All VG's"
    bl_idname = "gimi_tools.remove_all_vgs"
   

    def execute(self, context):
        selected_object = bpy.context.active_object

        if selected_object and selected_object.type == 'MESH':
            for group in selected_object.vertex_groups:
                selected_object.vertex_groups.remove(group)

        return {'FINISHED'}

class GIMI_TOOLS_OT_fill_vgs(bpy.types.Operator):
    bl_label = "Fill Vertex Groups"
    bl_idname = "gimi_tools.fill_vgs"
    bl_description = "Fill the VG's based on Largest input and sort the VG's"

    def execute(self, context):
        selected_object = bpy.context.active_object
        largest = context.scene.Largest_VG  
        ob = bpy.context.active_object
        ob.update_from_editmode()

        for vg in ob.vertex_groups:
            try:
                if int(vg.name.split(".")[0]) > largest:
                    largest = int(vg.name.split(".")[0])
            except ValueError:
                print("Vertex group not named as integer, skipping")

        missing = set([f"{i}" for i in range(largest + 1)]) - set([x.name.split(".")[0] for x in ob.vertex_groups])
        for number in missing:
            ob.vertex_groups.new(name=f"{number}")

        bpy.ops.object.vertex_group_sort()
        return {'FINISHED'}

class GIMI_TOOLS_OT_remove_unused_vgs(bpy.types.Operator):
    bl_label = "Remove Unused VG's"
    bl_idname = "gimi_tools.remove_unused_vgs"
    bl_description = "Remove all Empty VG's"

    def execute(self, context):
        if bpy.context.active_object:
            ob = bpy.context.active_object
            ob.update_from_editmode()

            vgroup_used = {i: False for i, k in enumerate(ob.vertex_groups)}

            for v in ob.data.vertices:
                for g in v.groups:
                    if g.weight > 0.0:
                        vgroup_used[g.group] = True

            for i, used in sorted(vgroup_used.items(), reverse=True):
                if not used:
                    ob.vertex_groups.remove(ob.vertex_groups[i])

            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "No objects selected")
            return {'CANCELLED'}
        
class OBJECT_OT_vertex_group_remap(bpy.types.Operator):
    bl_idname = "object.vertex_group_remap"
    bl_label = "Vertex Group Remap"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Remap the vertex groups between two selected objects"

    def execute(self, context):
        source = context.scene.vgm_source_object
        destination = context.scene.vgm_destination_object

        if not source or not destination:
            self.report({'ERROR'}, "Please, Select Source and Target object")
            return {'CANCELLED'}

        source_object = bpy.data.objects.get(source.name)
        destination_object = bpy.data.objects.get(destination.name)

        if not source_object or not destination_object:
            self.report({'ERROR'}, "Please, Select Source and Target object")
            return {'CANCELLED'}

   
        match_vertex_groups(source_object, destination_object)
        self.report({'INFO'}, "Vertex groups matched.")
        

        if destination_object and destination_object.type == 'MESH' and destination_object.vertex_groups:
            vertex_group_names = [vg.name for vg in destination_object.vertex_groups]
            print("Remapped VG's:", ", ".join(vertex_group_names))
        else:
            print("No vertex groups found in the target object.")

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.view_layer.objects.active = destination_object
        destination_object.select_set(True)

        return {'FINISHED'}

def calculate_vertex_influence_area(obj):
    vertex_area = np.zeros(len(obj.data.vertices))

    for face in obj.data.polygons:
        area_per_vertex = face.area / len(face.vertices)
        for vert_idx in face.vertices:
            vertex_area[vert_idx] += area_per_vertex

    return vertex_area

def get_all_weighted_centers(obj):
    vertex_influence_area = calculate_vertex_influence_area(obj)
    matrix_world = np.array(obj.matrix_world)

    def to_homogeneous(coord):
        return (coord.x, coord.y, coord.z, 1.0)

    vertex_coords = np.array([matrix_world @ to_homogeneous(vertex.co) for vertex in obj.data.vertices])[:, :3]
    num_vertices = len(obj.data.vertices)
    num_groups = len(obj.vertex_groups)

    weights = np.zeros((num_vertices, num_groups))
    for vertex in obj.data.vertices:
        for group in vertex.groups:
            weights[vertex.index, group.group] = group.weight

    weighted_areas = weights * vertex_influence_area[:, np.newaxis]
    total_weight_areas = weighted_areas.sum(axis=0)

    centers = {}
    for i, vgroup in enumerate(obj.vertex_groups):
        total_weight_area = total_weight_areas[i]
        if total_weight_area > 0:
            weighted_position_sum = (weighted_areas[:, i][:, np.newaxis] * vertex_coords).sum(axis=0)
            center = weighted_position_sum / total_weight_area
            centers[vgroup.name] = tuple(center)
            print(f"Center for {vgroup.name}: {center}")
        else:
            centers[vgroup.name] = None
            print(f"No weighted center for {vgroup.name}")

    return centers

def find_nearest_center(base_centers, target_center):
    best_match = None
    best_distance = float('inf')
    target_center = np.array(target_center)
    for base_group_name, base_center in base_centers.items():
        if base_center is None:
            continue
        base_center = np.array(base_center)
        distance = np.linalg.norm(target_center - base_center)
        if distance < best_distance:
            best_distance = distance
            best_match = base_group_name
    return best_match

def match_vertex_groups(source_obj, target_obj):
    for target_group in target_obj.vertex_groups:
        target_group.name = "unknown"
    source_centers = get_all_weighted_centers(source_obj)
    target_centers = get_all_weighted_centers(target_obj)

    for target_group in target_obj.vertex_groups:
        target_center = target_centers.get(target_group.name)
        if target_center is None:
            continue

        best_match = find_nearest_center(source_centers, target_center)

        if best_match:
            target_group.name = best_match
            print(f"Target group {target_group.index} renamed to {best_match}")

class QuickImportSettings(bpy.types.PropertyGroup):
    tri_to_quads: BoolProperty(
        name="Tri to Quads",
        default=False,
        description="Enable Tri to Quads"
    )#type: ignore 
    merge_by_distance: BoolProperty(
        name="Merge by Distance",
        default=False,
        description="Enable Merge by Distance"
    )#type: ignore 
    reset_rotation: BoolProperty(
        name="Reset Rotation (ZZZ)",
        default=False,
        description="Reset the rotation of the object upon import"
    ) #type: ignore 
    import_textures: BoolProperty(
        name="Import Textures",
        default=True,
        description="Apply Materials and Textures"
    ) #type: ignore 
    create_collection: BoolProperty(
        name="Create Collection",
        default=True,
        description="Create a new collection based on the folder name"
    ) #type: ignore e: ignore 


class TextureHandler:
    @staticmethod
    def convert_dds(context, file):
        """Import a file."""
        dds_options = context.scene.dds_options
        tex = import_dds.load_dds(
            file,
            invert_normals=dds_options.invert_normals,
            cubemap_layout=dds_options.cubemap_layout,
        )
        return tex

    @staticmethod
    def create_material(context, files, path):
        importedmeshes = []
        for file in files:
            mesh_name = bpy.path.display_name_from_filepath(os.path.join(path, file))
            mesh_name = mesh_name[:-7]

            if context.scene.quick_import_settings.import_textures:
                TextureHandler.convert_dds(context, file=os.path.join(path, file))

                material_name = "mat_" + mesh_name
                mat = TextureHandler.setup_texture(material_name, file)

             
                for obj in bpy.data.objects:
                    print(f"Checking {obj.name} against {mesh_name}")
                    if obj.name.startswith(mesh_name):
              
                        print(f"FOUND! Assigning material {mat} to {obj.name}")
                        obj.data.materials.append(bpy.data.materials.get(mat))
                        importedmeshes.append(obj)
            else:
                print(f"Skipping texture import for {file} as import_textures is disabled.")

        return importedmeshes
    
    @staticmethod
    def setup_texture(name, texture_name):
        """Creates a new material using that texture as base color, also sets alpha to none"""
        material = bpy.data.materials.new(name)
        material.use_nodes = True
        bsdf = material.node_tree.nodes["Principled BSDF"]
        bsdf.inputs[0].default_value = (1, 1, 1, 1)
        if bpy.app.version < (4, 0):
            bsdf.inputs[5].default_value = 0.0
        else:
            bsdf.inputs[5].default_value = (0.5, 0.5, 0.5)
        texImage = material.node_tree.nodes.new("ShaderNodeTexImage")
        texture_name = texture_name[:-4]
        texImage.image = bpy.data.images.get(texture_name)
        texImage.image.alpha_mode = "NONE"
        material.node_tree.links.new(texImage.outputs[0], bsdf.inputs[0])
        return material.name

class TextureHandler42:
    @staticmethod
    def create_material(context, files, path):
        importedmeshes = []
        for file in files:
            mesh_name = bpy.path.display_name_from_filepath(os.path.join(path, file))
            mesh_name = mesh_name[:-7]

            material_name = "mat_" + mesh_name
            mat = TextureHandler42.setup_texture(material_name, os.path.join(path, file))

            for obj in bpy.data.objects:
                if obj.name.startswith(mesh_name):
                    obj.data.materials.append(bpy.data.materials.get(mat))
                    importedmeshes.append(obj)

        return importedmeshes
    
    @staticmethod
    def setup_texture(name, texture_path):
        """Creates a new material using that texture as base color, also sets alpha to none"""
        material = bpy.data.materials.new(name)
        material.use_nodes = True
        bsdf = material.node_tree.nodes["Principled BSDF"]
        bsdf.inputs[0].default_value = (1, 1, 1, 1)
        bsdf.inputs[5].default_value = (0.5, 0.5, 0.5)
        texImage = material.node_tree.nodes.new("ShaderNodeTexImage")

        try:
            image = bpy.data.images.load(texture_path)
            texImage.image = image
            texImage.image.alpha_mode = "NONE"
            material.node_tree.links.new(texImage.outputs[0], bsdf.inputs[0])
        except Exception as e:
            print(f"Error loading image {texture_path}: {e}")
        
        return material.name
        
class GIMI_TOOLS_PT_quick_import_panel(bpy.types.Panel):
    bl_label = "Quick Import"
    bl_idname = "GIMI_TOOLS_PT_QuickImportPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'XXMI Scripts'
 
    def draw(self, context):
        layout = self.layout
        cfg = context.scene.quick_import_settings

        row = layout.row()
        row.operator("import_scene.3dmigoto_frame_analysis", text="Setup Character", icon='IMPORT')

        layout.prop(cfg, "tri_to_quads")
        layout.prop(cfg, "merge_by_distance")
        layout.prop(cfg, "reset_rotation")

        row = layout.row(align=True)
        row.prop(cfg, "import_textures")
        row.prop(cfg, "create_collection")

class QuickImport(Import3DMigotoFrameAnalysis):
    bl_idname = "import_scene.3dmigoto_frame_analysis"
    bl_label = "Quick Import for XXMI"
    bl_options = {"UNDO"}

    def execute(self, context):
        super().execute(context)
        folder = os.path.dirname(self.properties.filepath)
        print("------------------------")

        print(f"Found Folder: {folder}")
        files = os.listdir(folder)
        files = [f for f in files if f.endswith("Diffuse.dds")]
        print(f"List of files: {files}")

        if bpy.app.version < (4, 2, 0):
            importedmeshes = TextureHandler.create_material(context, files, folder)
        else:
            importedmeshes = TextureHandler42.create_material(context, files, folder)

        print(f"Imported meshes: {[obj.name for obj in importedmeshes]}")

        if context.scene.quick_import_settings.create_collection:
            collection_name = os.path.basename(folder)
            new_collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(new_collection)


            for obj in bpy.context.selected_objects:
                if obj.name.startswith(collection_name):
                    bpy.context.scene.collection.objects.unlink(obj)
                    new_collection.objects.link(obj)
                    print(f"Moved {obj.name} to collection {collection_name}")
                else:
                    print(f"Ignored {obj.name} as it does not match the collection name")

        if context.scene.quick_import_settings.reset_rotation:
            bpy.ops.object.select_all(action='SELECT')
            for obj in context.selected_objects:
                obj.rotation_euler = (0, 0, 0)

        if context.scene.quick_import_settings.tri_to_quads:
            bpy.ops.object.mode_set(mode='EDIT')          
            bpy.ops.mesh.select_all(action='SELECT') 
            bpy.ops.mesh.tris_convert_to_quads(uvs=True, vcols=True, seam=True, sharp=True, materials=True)
            bpy.ops.mesh.delete_loose()
            
        if context.scene.quick_import_settings.merge_by_distance:
            bpy.ops.object.mode_set(mode='EDIT')          
            bpy.ops.mesh.select_all(action='SELECT') 
            bpy.ops.mesh.remove_doubles(use_sharp_edge_from_normals=True)   
            bpy.ops.mesh.delete_loose()
            
        if context.scene.quick_import_settings.import_textures:
            bpy.ops.object.mode_set(mode='EDIT')          
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.delete_loose()
            bpy.ops.object.mode_set(mode='OBJECT')
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.spaces.active.shading.type = 'MATERIAL'

        return {"FINISHED"}
    
class OBJECT_OT_separate_by_material_and_rename(bpy.types.Operator):
    """Separate by Material and Rename"""
    bl_idname = "object.separate_by_material_and_rename"
    bl_label = "Separate by Material and Rename"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.separate(type='MATERIAL')
        bpy.ops.object.mode_set(mode='OBJECT')


        for o in bpy.context.selected_objects:
            material_name = o.active_material.name.replace("mat_", "")
            material_name = material_name.replace("Diffuse", "").strip()
            o.name = material_name

        return {'FINISHED'}
    
    def invoke(self, context, event):
        if event.type == 'P':
            return context.window_manager.invoke_props_dialog(self)
        else:
            return self.execute(context)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Want to proceed?")

def menu_func(self, context):
    self.layout.operator(OBJECT_OT_separate_by_material_and_rename.bl_idname)


addon_keymaps = []
        
def menu_func_import(self, context):
    self.layout.operator(QuickImport.bl_idname, text="Quick Import for XXMI")   


classes = [
    GIMI_TOOLS_PT_main_panel,
    GIMI_TOOLS_OT_fill_vgs,
    GIMI_TOOLS_OT_remove_unused_vgs,
    GIMI_TOOLS_OT_remove_all_vgs,
    GIMI_TOOLS_PT_quick_import_panel,
    OBJECT_OT_transfer_properties,
    OBJECT_OT_vertex_group_remap,
    OBJECT_OT_merge_vertex_groups,
    QuickImport,
    QuickImportSettings,
    OBJECT_OT_separate_by_material_and_rename
]

def register_classes():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister_classes():
    for cls in classes:
        bpy.utils.unregister_class(cls)

def register():
    register_classes()
    
    # Pointers
    cfg = bpy.types.Scene
    cfg.show_vertex = bpy.props.BoolProperty(name="Show Vertex", default=False)
    cfg.show_remap = bpy.props.BoolProperty(name="Show Remap", default=False)
    cfg.show_transfer = bpy.props.BoolProperty(name="Show Transfer", default=False)
    cfg.base_collection = bpy.props.PointerProperty(type=bpy.types.Collection, description="Base Collection")
    cfg.target_collection = bpy.props.PointerProperty(type=bpy.types.Collection, description="Target Collection")
    cfg.base_objectproperties = bpy.props.PointerProperty(type=bpy.types.Object, description="Base Object")
    cfg.target_objectproperties = bpy.props.PointerProperty(type=bpy.types.Object, description="Target Object")
    cfg.transfer_mode = bpy.props.EnumProperty(
        items=[
            ('COLLECTION', 'Collection Transfer', 'Transfer properties between collections'),
            ('MESH', 'Mesh Transfer', 'Transfer properties between meshes')
        ],
        default='MESH',
        description="Mode of Transfer"
    )
    cfg.base_object = bpy.props.PointerProperty(type=bpy.types.Object, description="Base Object for operations")
    cfg.target_object = bpy.props.PointerProperty(type=bpy.types.Object, description="Target Object for operations")
    cfg.Largest_VG = bpy.props.IntProperty(description="Value for Largest Vertex Group")
    cfg.bone_object = bpy.props.PointerProperty(type=bpy.types.Object, description="Object containing bones")
    cfg.vgm_source_object = bpy.props.PointerProperty(type=bpy.types.Object, description="Source Object for Vertex Group Mapping")
    cfg.vgm_destination_object = bpy.props.PointerProperty(type=bpy.types.Object, description="Destination Object for Vertex Group Mapping")
    cfg.merge_mode = bpy.props.EnumProperty(items=[
        ('MODE1', 'Mode 1: Single VG', 'Merge based on specific vertex groups'),
        ('MODE2', 'Mode 2: By Range ', 'Merge based on a range of vertex groups'),
        ('MODE3', 'Mode 3: All VG', 'Merge all vertex groups')],
        default='MODE3')
    cfg.vertex_groups = bpy.props.StringProperty(name="Vertex Groups", default="")
    cfg.smallest_group_number = bpy.props.IntProperty(name="Smallest Group", default=0)
    cfg.largest_group_number = bpy.props.IntProperty(name="Largest Group", default=999)
    cfg.quick_import_settings = bpy.props.PointerProperty(type=QuickImportSettings)
    
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.VIEW3D_MT_object.append(menu_func)
    
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='Object Mode', space_type='EMPTY')
    kmi = km.keymap_items.new(OBJECT_OT_separate_by_material_and_rename.bl_idname, 'P', 'PRESS')
    addon_keymaps.append((km, kmi))

def unregister():
    unregister_classes()
    
    cfg = bpy.types.Scene
    del cfg.show_vertex
    del cfg.show_remap
    del cfg.show_transfer
    del cfg.base_object
    del cfg.target_object
    del cfg.Largest_VG
    del cfg.bone_object
    del cfg.vgm_source_object
    del cfg.vgm_destination_object
    del cfg.merge_mode
    del cfg.vertex_groups
    del cfg.smallest_group_number
    del cfg.largest_group_number
    del cfg.quick_import_settings
    del cfg.base_collection
    del cfg.target_collection
    del cfg.base_objectproperties
    del cfg.target_objectproperties
    del cfg.transfer_mode
    
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.VIEW3D_MT_object.remove(menu_func)
    
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

if __name__ == "__main__":
    register()