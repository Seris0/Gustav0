
#Author: Gustav0, LeoTorreZ
#Special thanks to Silent for providing several scripts and 3dframeanalyse, and LeoTools for QuickImport.




import os
import bpy
from bpy.props import PointerProperty, StringProperty, EnumProperty, CollectionProperty, BoolProperty
from bpy.types import Object, Operator, Panel, PropertyGroup
from bpy_extras.io_utils import unpack_list, ImportHelper, ExportHelper, axis_conversion
from blender_dds_addon import import_dds
from bpy.utils import register_class, unregister_class
 

try:
    from XXMI_Tools.migoto.operators import Import3DMigotoFrameAnalysis
except ImportError:
    module_name = "XXMI-Tools.migoto.operators"
    Import3DMigotoFrameAnalysis = __import__(module_name, fromlist=['Import3DMigotoFrameAnalysis']).Import3DMigotoFrameAnalysis

bl_info = {
    "name": "XXMI Scripts & Quick Import",
    "author": "Gustav0, LeoTorreZ",
    "version": (1, 0),
    "blender": (3, 6, 2),
    "description": "Script Compilation",
    "category": "Object",
}


class GIMI_TOOLS_PT_main_panel(bpy.types.Panel):
    bl_label = "XXMI Tools"
    bl_idname = "GIMI_TOOLS_PT_MainPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'XXMI Scripts'
    # bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        box = layout.box()
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
        # Merge VG's Modes
        layout.prop(context.scene, "merge_mode", text="Merge Mode")
        if context.scene.merge_mode == 'MODE1':
            layout.prop(context.scene, "vertex_groups", text="Vertex Groups")
        elif context.scene.merge_mode == 'MODE2':
            layout.prop(context.scene, "smallest_group_number", text="Smallest Group")
            layout.prop(context.scene, "largest_group_number", text="Largest Group")
        layout.operator("object.merge_vertex_groups", text="Merge Vertex")
        # VG Remap
        box = layout.box()
        box.label(text="Vertex Group REMAP", icon='FILE_REFRESH')
        row = box.row()
        row.prop_search(context.scene, "vgm_source_object", bpy.data, "objects", text="Source")
        row = box.row()
        row.prop_search(context.scene, "vgm_destination_object", bpy.data, "objects", text="Target")
        row = box.row()
        row.operator("object.vertex_group_remap", text="Run Remap")  
          
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
    bl_description = "Remap the vg's between 2 selected objects"

    def execute(self, context):
        source = context.scene.vgm_source_object
        destination = context.scene.vgm_destination_object

        if not source or not destination:
            self.report({'ERROR'}, "Please, Select Target and Source object")
            return {'CANCELLED'}

        source_object = bpy.data.objects.get(source.name)
        destination_object = bpy.data.objects.get(destination.name)

        if not source_object or not destination_object:
            self.report({'ERROR'}, "Please, Select Target and Source object")
            return {'CANCELLED'}

        original_vg_length = len(source_object.vertex_groups)

        source_vertices = collect_vertices(source_object)
        tree = KDTree(list(source_vertices.keys()), 3)

        candidates = [{} for _ in range(len(destination_object.vertex_groups))]
        destination_vertices = collect_vertices(destination_object)
        for vertex in destination_vertices:
            nearest_source = source_vertices[tree.get_nearest(vertex)[1]]
            for group, weight in destination_vertices[vertex]:
                if weight == 0:
                    continue
                nearest_source_group, smallest_distance = nearest_group(weight, nearest_source)

                if nearest_source_group in candidates[group]:
                    x = candidates[group][nearest_source_group]
                    candidates[group][nearest_source_group] = [x[0] + smallest_distance, x[1] + 1]
                else:
                    candidates[group][nearest_source_group] = [smallest_distance, 1]

        best = []
        for group in candidates:
            best_group = -1
            highest_overlap = -1
            for c in group:
                if group[c][1] > highest_overlap:
                    best_group = c
                    highest_overlap = group[c][1]
            best.append(best_group)

        for i, vg in enumerate(destination_object.vertex_groups):
            if best[i] == -1:
                print(f"Removing empty group {vg.name}")
                destination_object.vertex_groups.remove(vg)
            else:
                print(f"Renaming {vg.name} to {best[i]}")
                vg.name = f"x{str(best[i])}"

        for i, vg in enumerate(destination_object.vertex_groups):
            vg.name = vg.name[1:]

        missing = set([f"{i}" for i in range(original_vg_length)]) - set([x.name.split(".")[0] for x in destination_object.vertex_groups])
        for number in missing:
            destination_object.vertex_groups.new(name=f"{number}")

        bpy.context.view_layer.objects.active = destination_object
        bpy.ops.object.vertex_group_sort()

        return {'FINISHED'}

def collect_vertices(obj):
    results = {}
    for v in obj.data.vertices:
        results[(v.co.x, v.co.y, v.co.z)] = [(vg.group, vg.weight) for vg in v.groups]
    return results

def nearest_group(weight, nearest_source):
    nearest_group = -1
    smallest_difference = 10000000000
    for source_group, source_weight in nearest_source:
        if abs(weight - source_weight) < smallest_difference:
            smallest_difference = abs(weight - source_weight)
            nearest_group = source_group
    return nearest_group, smallest_difference

class KDTree(object):
    def __init__(self, points, dim, dist_sq_func=None):
        if dist_sq_func is None:
            dist_sq_func = lambda a, b: sum((x - b[i]) ** 2
                                            for i, x in enumerate(a))

        def make(points, i=0):
            if len(points) > 1:
                points.sort(key=lambda x: x[i])
                i = (i + 1) % dim
                m = len(points) >> 1
                return [make(points[:m], i), make(points[m + 1:], i),
                        points[m]]
            if len(points) == 1:
                return [None, None, points[0]]

        def add_point(node, point, i=0):
            if node is not None:
                dx = node[2][i] - point[i]
                for j, c in ((0, dx >= 0), (1, dx < 0)):
                    if c and node[j] is None:
                        node[j] = [None, None, point]
                    elif c:
                        add_point(node[j], point, (i + 1) % dim)

        import heapq
        def get_knn(node, point, k, return_dist_sq, heap, i=0, tiebreaker=1):
            if node is not None:
                dist_sq = dist_sq_func(point, node[2])
                dx = node[2][i] - point[i]
                if len(heap) < k:
                    heapq.heappush(heap, (-dist_sq, tiebreaker, node[2]))
                elif dist_sq < -heap[0][0]:
                    heapq.heappushpop(heap, (-dist_sq, tiebreaker, node[2]))
                i = (i + 1) % dim
            
                for b in (dx < 0, dx >= 0)[:1 + (dx * dx < -heap[0][0])]:
                    get_knn(node[b], point, k, return_dist_sq,
                            heap, i, (tiebreaker << 1) | b)
            if tiebreaker == 1:
                return [(-h[0], h[2]) if return_dist_sq else h[2]
                        for h in sorted(heap)][::-1]

        def walk(node):
            if node is not None:
                for j in 0, 1:
                    for x in walk(node[j]):
                        yield x
                yield node[2]

        self._add_point = add_point
        self._get_knn = get_knn
        self._root = make(points)
        self._walk = walk

    def __iter__(self):
        return self._walk(self._root)

    def add_point(self, point):
        if self._root is None:
            self._root = [None, None, point]
        else:
            self._add_point(self._root, point)

    def get_knn(self, point, k, return_dist_sq=True):
        return self._get_knn(self._root, point, k, return_dist_sq, [])

    def get_nearest(self, point, return_dist_sq=True):
        l = self._get_knn(self._root, point, 1, return_dist_sq, [])
        return l[0] if len(l) else None

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
    apply_textures: BoolProperty(
        name="Apply Textures",
        default=True,
        description="Apply Materials and Textures"
    ) #type: ignore 
    create_collection: BoolProperty(
        name="Create Collection",
        default=False,
        description="Create a new collection based on the folder name"
    ) #type: ignore e: ignore 


class TextureHandler:
    @staticmethod
    def new_material(name, texture_name):
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
            mesh_name = bpy.path.display_name_from_filepath(os.path.join(path, file))
            mesh_name = mesh_name[:-7]

            if context.scene.quick_import_settings.apply_textures:
                TextureHandler.import_dafile(context, file=os.path.join(path, file))

                material_name = "mat_" + mesh_name
                mat = TextureHandler.new_material(material_name, file)

             
                for obj in bpy.data.objects:
                    print(f"Checking {obj.name} against {mesh_name}")
                    if obj.name.startswith(mesh_name):
              
                        print(f"FOUND! Assigning material {mat} to {obj.name}")
                        obj.data.materials.append(bpy.data.materials.get(mat))
                        importedmeshes.append(obj)
            else:
                print(f"Skipping texture import for {file} as apply_textures is disabled.")

        return importedmeshes

class GIMI_TOOLS_PT_quick_import_panel(bpy.types.Panel):
    bl_label = "Quick Import"
    bl_idname = "GIMI_TOOLS_PT_QuickImportPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'XXMI Scripts'
 
    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        row.operator("import_scene.3dmigoto_frame_analysis", text="Setup Character", icon='IMPORT')

        layout.prop(context.scene.quick_import_settings, "tri_to_quads")
        layout.prop(context.scene.quick_import_settings, "merge_by_distance")
        layout.prop(scene.quick_import_settings, "reset_rotation")

        row = layout.row(align=True)
        row.prop(context.scene.quick_import_settings, "apply_textures")
        row.prop(context.scene.quick_import_settings, "create_collection")

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

        importedmeshes = TextureHandler.import_files(context, files, folder)
        print(f"Imported meshes: {[obj.name for obj in importedmeshes]}")

        if context.scene.quick_import_settings.create_collection:
            collection_name = os.path.basename(folder)
            new_collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(new_collection)

            # Move all selected objects (imported meshes) to the new collection if their name matches the collection name
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
            
        if context.scene.quick_import_settings.apply_textures:
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


def register():

    classes = [
        GIMI_TOOLS_PT_main_panel,
        GIMI_TOOLS_OT_fill_vgs,
        GIMI_TOOLS_OT_remove_unused_vgs,
        GIMI_TOOLS_OT_remove_all_vgs,
        GIMI_TOOLS_PT_quick_import_panel,
        OBJECT_OT_vertex_group_remap,
        OBJECT_OT_merge_vertex_groups,
        QuickImport,
        QuickImportSettings,
        OBJECT_OT_separate_by_material_and_rename
    ]

    for cls in classes:
        bpy.utils.register_class(cls)

    #pointers
    bpy.types.Scene.base_object = bpy.props.PointerProperty(type=bpy.types.Object, description="Base Object for operations")
    bpy.types.Scene.target_object = bpy.props.PointerProperty(type=bpy.types.Object, description="Target Object for operations")
    bpy.types.Scene.Largest_VG = bpy.props.IntProperty(description="Value for Largest Vertex Group")
    bpy.types.Scene.bone_object = bpy.props.PointerProperty(type=bpy.types.Object, description="Object containing bones")
    bpy.types.Scene.vgm_source_object = bpy.props.PointerProperty(type=bpy.types.Object, description="Source Object for Vertex Group Mapping")
    bpy.types.Scene.vgm_destination_object = bpy.props.PointerProperty(type=bpy.types.Object, description="Destination Object for Vertex Group Mapping")
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    
    bpy.types.Scene.merge_mode = bpy.props.EnumProperty(items=[
        ('MODE1', 'Mode 1: Single VG', 'Merge based on specific vertex groups'),
        ('MODE2', 'Mode 2: By Range ', 'Merge based on a range of vertex groups'),
        ('MODE3', 'Mode 3: All VG', 'Merge all vertex groups')],
        default='MODE3')
    bpy.types.Scene.vertex_groups = bpy.props.StringProperty(name="Vertex Groups", default="")
    bpy.types.Scene.smallest_group_number = bpy.props.IntProperty(name="Smallest Group", default=0)
    bpy.types.Scene.largest_group_number = bpy.props.IntProperty(name="Largest Group", default=999)
    bpy.types.Scene.quick_import_settings = bpy.props.PointerProperty(type=QuickImportSettings)
    
    bpy.types.VIEW3D_MT_object.append(menu_func)
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='Object Mode', space_type='EMPTY')
    kmi = km.keymap_items.new(OBJECT_OT_separate_by_material_and_rename.bl_idname, 'P', 'PRESS')
    addon_keymaps.append((km, kmi))

def unregister():
    classes = [
        GIMI_TOOLS_PT_main_panel,
        GIMI_TOOLS_OT_fill_vgs,
        GIMI_TOOLS_OT_remove_unused_vgs,
        GIMI_TOOLS_OT_remove_all_vgs,
        GIMI_TOOLS_PT_quick_import_panel,
        OBJECT_OT_vertex_group_remap,
        OBJECT_OT_merge_vertex_groups,
        QuickImport,
        QuickImportSettings,
        OBJECT_OT_separate_by_material_and_rename
    ]

    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.base_object
    del bpy.types.Scene.target_object
    del bpy.types.Scene.Largest_VG
    del bpy.types.Scene.bone_object
    del bpy.types.Scene.vgm_source_object
    del bpy.types.Scene.vgm_destination_object
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    
    del bpy.types.Scene.merge_mode
    del bpy.types.Scene.vertex_groups
    del bpy.types.Scene.smallest_group_number
    del bpy.types.Scene.largest_group_number
    del bpy.types.Scene.quick_import_settings
    
    bpy.types.VIEW3D_MT_object.remove(menu_func)
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

if __name__ == "__main__":
    register()