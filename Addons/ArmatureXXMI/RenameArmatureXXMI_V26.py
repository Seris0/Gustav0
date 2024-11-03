#Author: Gustav0_

#Set up armature for certain anime games

# Main matching logic get from the gigachad Comilarex https://gamebanana.com/tools/15699

import bpy
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import PointerProperty, EnumProperty, BoolProperty
from mathutils import Vector
import numpy as np
import time

bl_info = {
    "name": "ArmatureXXMI",
    "author": "Gustav",
    "version": (2, 6, 2),
    "blender": (3, 6, 2),
    "description": "Matches Armature based on weight paint centroids and surface area.",
    "category": "Object",
}

#MARK: PropertyGroups
class ArmatureMatchingProperties(PropertyGroup):
    armature_mode: EnumProperty(
        name="Armature Mode",
        description="Select the armature mode",
        items=[
            ('MERGED', "Merged Armature", "All components vg's in a single armature"),
            ('PER_COMPONENT', "Per-Component", "An armature for each unique component")
        ],
        default='MERGED'
    )#type: ignore
    mode: EnumProperty(
        name="Mode",
        description="Select the mode for processing",
        items=[
            ('HONKAI', "Honkai Star Rail", "Process for Honkai Star Rail"),
            ('ZENLESS', "Zenless Zone Zero", "Process for Zenless Zone Zero"),
            ('GENSHIN', "Genshin Impact", "Process for Genshin Impact"),
            ("WUWA", "Wuthering Waves", "Process for Wuthering Waves")
        ],
        default='GENSHIN'
    )#type: ignore
    ignore_hair: BoolProperty(
        name="Ignore Hair",
        description="Ignore meshes containing 'hair' in their names",
        default=False
    ) #type: ignore
    ignore_head: BoolProperty(
        name="Ignore Head",
        description="Ignore meshes containing 'head' in their names",
        default=False
    ) #type: ignore
    base_collection: PointerProperty(
        name="Base Collection",
        type=bpy.types.Collection,
        description="Base collection for ARMATURE matching"
    ) #type: ignore
    target_collection: PointerProperty(
        name="Target Collection",
        type=bpy.types.Collection,
        description="Target collection for Armature paint matching"
    ) #type: ignore
    armature: PointerProperty(
        name="Armature",
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == 'ARMATURE',
        description="Armature to rename bones"
    ) #type: ignore

#MARK: Matching
class ArmatureMatchingOperator(Operator):
    """Matches Vertex groups and renames bones in the armature"""
    bl_idname = "object.armature_matching"
    bl_label = "Match Armature"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.armature_matching_props
        base_collection = props.base_collection
        target_collection = props.target_collection
        armature_obj = props.armature
        mode = props.mode
        ignore_hair = props.ignore_hair
        ignore_head = props.ignore_head
        armature_mode = props.armature_mode

        print(f"Base Collection: {base_collection}")
        print(f"Target Collection: {target_collection}")
        print(f"Armature Object: {armature_obj}")
        print(f"Mode: {mode}")
        print(f"Armature Mode: {armature_mode}")

        if base_collection and target_collection and armature_obj:
            if armature_obj.type == 'ARMATURE':
                print("Processing target collection...")
                target_obj = process_target_collection(target_collection, mode)
                print("Processing base collection...")
                base_obj = process_base_collection(base_collection, mode, ignore_hair, ignore_head, armature_mode)
                
                if base_obj and target_obj:
                    print("Starting vertex group matching...")
                    matching_info = match_vertex_groups(base_obj, target_obj)
                    print(f"Matching Info: {matching_info}")
                    rename_armature_bones(matching_info, armature_obj)
                    self.report({'INFO'}, "Vertex groups matched and armature bones renamed.")
                    
                    meshes_to_delete = [obj for obj in armature_obj.children if obj.type == 'MESH']
                    bpy.ops.object.select_all(action='DESELECT')
                    for mesh in meshes_to_delete:
                        mesh.select_set(True)
                    bpy.ops.object.delete()

                    if armature_obj.name not in base_collection.objects:
                        base_collection.objects.link(armature_obj)
                    
                    for collection in armature_obj.users_collection:
                        if collection != base_collection:
                            collection.objects.unlink(armature_obj)
                    
                    new_armature_name = f"{base_collection.name}_Armature"
                    armature_obj.name = new_armature_name
                    armature_obj.show_in_front = True

                    self.report({'INFO'}, f"Armature moved to base collection and renamed to {new_armature_name}.")


                    for obj in base_collection.objects:
                        if obj.type == 'MESH':
                            modifier = obj.modifiers.new(name="Armature", type='ARMATURE')
                            modifier.object = armature_obj
                            self.report({'INFO'}, f"Added Armature modifier to {obj.name}.")
                else:
                    self.report({'ERROR'}, "Failed to process collections.")
            else:
                self.report({'ERROR'}, "Invalid object type for armature.")
        else:
            self.report({'ERROR'}, "One or more collections not found.")

        return {'FINISHED'}

def process_target_collection(collection, mode):
    target_objs = [obj for obj in collection.objects if obj.type == 'MESH']

    if mode == 'GENSHIN':
        ao_meshes = [obj for obj in target_objs if obj.name.startswith('AO')]
        for obj in ao_meshes:
            collection.objects.unlink(obj)  
            bpy.data.objects.remove(obj, do_unlink=True)  

    target_objs = [obj for obj in collection.objects if obj.type == 'MESH']

    objects_to_remove = []
    for obj in target_objs:
        name_lower = obj.name.lower()
        if any(keyword in name_lower for keyword in ['hairshadow', 'weapon', 'face', 'eye', 'effect']):
            if not ('weapon' in name_lower and 'body' in name_lower):
                objects_to_remove.append(obj)

    for obj in objects_to_remove:
        collection.objects.unlink(obj)
        bpy.data.objects.remove(obj, do_unlink=True)

    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT')

    target_objs = [obj for obj in collection.objects if obj.type == 'MESH']
    for obj in target_objs:
        if obj.name in bpy.data.objects:
            obj.select_set(True)

    if len(target_objs) > 0:
        bpy.context.view_layer.objects.active = target_objs[0]
        bpy.ops.object.join()

        return bpy.context.view_layer.objects.active
    else:
        return None

def process_base_collection(collection, mode, ignore_hair, ignore_head, armature_mode):
    base_objs = [obj for obj in collection.objects if obj.type == 'MESH']
    
    if ignore_hair:
        print("Ignoring hair meshes...")
        base_objs = [obj for obj in base_objs if 'hair' not in obj.name.lower()]
    if ignore_head:
        print("Ignoring head meshes...")
        base_objs = [obj for obj in base_objs if 'head' not in obj.name.lower()]

    if mode in ['HONKAI']:
        if armature_mode in ['MERGED', 'PER_COMPONENT']:
            body_meshes = [obj for obj in base_objs if 'body' in obj.name.lower()]
            other_meshes = [obj for obj in base_objs if 'body' not in obj.name.lower()]
            
            if body_meshes:
                bpy.ops.object.select_all(action='DESELECT')
                for obj in body_meshes:
                    obj.select_set(True)
                bpy.context.view_layer.objects.active = body_meshes[0]
                bpy.ops.object.join()
                joined_body_mesh = bpy.context.view_layer.objects.active
                base_objs = [joined_body_mesh] + other_meshes
            else:
                other_meshes = base_objs
            
            for obj in other_meshes:
                mesh_name = obj.name.split('-')[0]
                for vg in obj.vertex_groups:
                    if not vg.name.startswith(mesh_name + "_"):
                        vg.name = f"{mesh_name}_{vg.name}"
                if not obj.name.startswith(mesh_name + "_"):
                    obj.name = f"{mesh_name}_{obj.name}"

    elif mode in ['GENSHIN', 'WUWA', 'ZENLESS']:
        if armature_mode == 'MERGED':
            bpy.ops.object.select_all(action='DESELECT')
            for obj in base_objs:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = base_objs[0]
            bpy.ops.object.join()
            return bpy.context.view_layer.objects.active
        
        elif armature_mode == 'PER_COMPONENT':
            for obj in base_objs:
                mesh_name = obj.name.split('-')[0]
                for vg in obj.vertex_groups:
                    if not vg.name.startswith(mesh_name + "_"):
                        vg.name = f"{mesh_name}_{vg.name}"
                # Remove the following line to prevent double renaming
                # if not obj.name.startswith(mesh_name + "_"):
                #     obj.name = f"{mesh_name}_{obj.name}"

    bpy.ops.object.select_all(action='DESELECT')
    for obj in base_objs:
        obj.select_set(True)
    
    if len(base_objs) > 0:
        bpy.context.view_layer.objects.active = base_objs[0]
        bpy.ops.object.join()
        
        joined_obj = bpy.context.view_layer.objects.active
        return joined_obj
    else:
        return None
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
        return np.array([coord.x, coord.y, coord.z, 1.0])

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
            centers[vgroup.name] = center
            print(f"Center for {vgroup.name}: {center}")
        else:
            centers[vgroup.name] = None
            print(f"No weighted center for {vgroup.name}")

    return centers

def find_nearest_center(base_centers, target_center):
    best_match = None
    best_distance = float('inf')
    for base_group_name, base_center in base_centers.items():
        if base_center is None:
            continue
        distance = np.linalg.norm(target_center - base_center)
        if distance < best_distance:
            best_distance = distance
            best_match = base_group_name
    return best_match

def match_vertex_groups(base_obj, target_obj):
    matching_info = {}

    base_centers = get_all_weighted_centers(base_obj)
    target_centers = get_all_weighted_centers(target_obj)

    for target_group_name, target_center in target_centers.items():
        if target_center is None:
            continue

        best_match = find_nearest_center(base_centers, target_center)

        if best_match:
            print(f"Target group {target_group_name} matched with base group {best_match}")
            matching_info[target_group_name] = best_match

    return matching_info
def rename_armature_bones(matching_info, armature_obj):
    bpy.ops.object.mode_set(mode='OBJECT')
    armature = armature_obj.data

    for bone in armature.bones:
        if bone.name in matching_info:
            new_name = matching_info[bone.name]
            print(f"Renaming bone {bone.name} to {new_name}")
            bone.name = new_name


#MARK: Mirror
class MirrorArmatureOperator(Operator):
    """Mirror Armature Object"""
    bl_idname = "object.mirror_armature"
    bl_label = "Mirror Armature"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.armature_matching_props
        armature_obj = props.armature

        if armature_obj and armature_obj.type == 'ARMATURE':
            bpy.context.view_layer.objects.active = armature_obj
            bpy.ops.object.select_all(action='DESELECT')
            armature_obj.select_set(True)
            bpy.context.view_layer.objects.active = armature_obj
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.transform.mirror(orient_type='GLOBAL', constraint_axis=(True, False, False))
            self.report({'INFO'}, "Armature mirrored.")
        else:
            self.report({'ERROR'}, "No valid armature object selected.")

        return {'FINISHED'}


#MARK: Armature > Character
class SetupCharacterForArmatureOperator(Operator):
    """Set up character for armature"""
    bl_idname = "object.setup_character_for_armature"
    bl_label = "Setup Character for Armature"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.armature_matching_props
        base_collection = props.base_collection
        mode = props.mode
        armature_mode = props.armature_mode
        ignore_hair = props.ignore_hair
        ignore_head = props.ignore_head
        armature_obj = props.armature

        print(f"Base Collection: {base_collection}")
        print(f"Mode: {mode}")
        print(f"Armature Mode: {armature_mode}")

        if bpy.context.object and bpy.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        if base_collection:
            base_objs = [obj for obj in base_collection.objects if obj.type == 'MESH']

            if ignore_hair:
                print("Ignoring hair meshes...")
                base_objs = [obj for obj in base_objs if 'hair' not in obj.name.lower()]
            if ignore_head:
                print("Ignoring head meshes...")
                base_objs = [obj for obj in base_objs if 'head' not in obj.name.lower()]

            try:
                if armature_obj:
                    for obj in base_objs:
                        if obj and obj.name in bpy.data.objects:
                            if not any(mod.type == 'ARMATURE' for mod in obj.modifiers):
                                modifier = obj.modifiers.new(name="Armature", type='ARMATURE')
                                modifier.object = armature_obj
                                bpy.context.view_layer.objects.active = obj
                                bpy.ops.object.parent_set(type='ARMATURE')
            except Exception as e:
                print(f"Failed to add armature to meshes: {e}")

            if armature_mode == 'PER_COMPONENT':
                for obj in base_objs:
                    if obj and obj.name in bpy.data.objects:
                        base_obj_name = obj.name.split('-')[0]
                        for vg in obj.vertex_groups:
                            if not vg.name.startswith(f"{base_obj_name}_"):
                                vg.name = f"{base_obj_name}_{vg.name}"

            elif mode == 'HONKAI':
                for obj in base_objs:
                    if obj and obj.name in bpy.data.objects:
                        base_obj_name = obj.name.split('-')[0]
                        if 'body' not in obj.name.lower():
                            for vg in obj.vertex_groups:
                                if not vg.name.startswith(f"{base_obj_name}_"):
                                    vg.name = f"{base_obj_name}_{vg.name}"

            elif mode not in {'GENSHIN', 'WUWA', 'ZENLESS'}:
                for obj in base_objs:
                    if obj and obj.name in bpy.data.objects:
                        base_obj_name = obj.name.split('-')[0]
                        if 'body' not in obj.name.lower():
                            for vg in obj.vertex_groups:
                                if not vg.name.startswith(f"{base_obj_name}_"):
                                    vg.name = f"{base_obj_name}_{vg.name}"

            self.report({'INFO'}, "Character set up for armature.")
        else:
            self.report({'ERROR'}, "Base collection not found.")

        return {'FINISHED'}

#MARK: CLEAN ARMATURE    
class CleanArmatureOperator(bpy.types.Operator):
    """Clean Armature Object by removing bones not linked to any vertex group, except those with specified prefixes"""
    bl_idname = "object.clean_armature"
    bl_label = "Clean Armature"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        print("Executing CleanArmatureOperator...")

        props = context.scene.armature_matching_props
        print(f"Weight paint matching properties: {props}")

        armature_obj = props.armature
        print(f"Armature object: {armature_obj}")

        if armature_obj and armature_obj.type == 'ARMATURE':
            print("Valid armature object found, setting to EDIT mode...")
            bpy.context.view_layer.objects.active = armature_obj
            bpy.ops.object.mode_set(mode='EDIT')
            armature = armature_obj.data
            print(f"Armature data: {armature}")

            vertex_group_names = set()
            for obj in bpy.data.objects:
                if obj.type == 'MESH' and obj.find_armature() == armature_obj:
                    vertex_group_names.update(vg.name for vg in obj.vertex_groups)

            print(f"Vertex groups: {vertex_group_names}")

            prefixes_to_exclude = ("Shoulder", "Scapula", "Knee", "Elbow", "UpperArm", "Clavicle", "Calf", "Forearm", "Thigh")
            bones_to_delete = [
                bone for bone in armature.edit_bones
                if bone.name not in vertex_group_names and not any(prefix.lower() in bone.name.lower() for prefix in prefixes_to_exclude)
            ]
            print(f"Bones to delete: {[bone.name for bone in bones_to_delete]}")

            for bone in bones_to_delete:
                print(f"Deleting bone: {bone.name}")
                armature.edit_bones.remove(bone)

            print("Setting mode back to OBJECT mode...")
            bpy.ops.object.mode_set(mode='OBJECT')
            self.report({'INFO'}, f"Deleted {len(bones_to_delete)} bones not linked to any vertex group.")
        else:
            print("No valid armature object selected.")
            self.report({'ERROR'}, "No valid armature object selected.")

        print("Finished CleanArmatureOperator execution.")
        return {'FINISHED'}
    
#MARK: SPLIT MESH
class SplitMeshByVertexGroupsOperator(Operator):
    """Split the Mesh based on the Vertex Names"""
    bl_idname = "object.split_mesh_by_vertex_groups"
    bl_label = "Split Mesh by Vertex Groups"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        start_time = time.time()
        props = context.scene.armature_matching_props
        base_collection = props.base_collection
        
        if not base_collection:
            self.report({'ERROR'}, "Base collection not found.")
            return {'CANCELLED'}
        
        base_objs = [obj for obj in base_collection.objects if obj.type == 'MESH']
        for obj in base_objs:
            rename_start = time.time()
            self.rename_mesh_based_on_vertex_groups(obj, base_collection)
            rename_end = time.time()
            print(f"Time to rename mesh based on vertex groups: {rename_end - rename_start} seconds")
        
        end_time = time.time()
        print(f"Total execution time: {end_time - start_time} seconds")
        self.report({'INFO'}, "Mesh split by vertex groups.")
        return {'FINISHED'}

    @staticmethod
    def is_numeric(s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    @staticmethod
    def remove_unused_vertex_groups(obj):
        obj.update_from_editmode()
        vgroup_used = {i: False for i, _ in enumerate(obj.vertex_groups)}
        for v in obj.data.vertices:
            for g in v.groups:
                if g.weight > 0.0:
                    vgroup_used[g.group] = True
        for i, used in sorted(vgroup_used.items(), reverse=True):
            if not used:
                obj.vertex_groups.remove(obj.vertex_groups[i])

    @staticmethod
    def separate_mesh_by_vertex_group_prefix(obj):
        separate_start = time.time()
        vertex_groups_dict = {}
        for vg in obj.vertex_groups:
            parts = vg.name.split('_')
            prefix = parts[0] if not parts[0].isdigit() else "numeric_groups"
            if prefix not in vertex_groups_dict:
                vertex_groups_dict[prefix] = []
            vertex_groups_dict[prefix].append(vg.index)
        
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        separated_objects = []
        
        mesh = obj.data
        bpy.ops.mesh.select_all(action='DESELECT')

        for prefix, group_indices in vertex_groups_dict.items():
            bpy.ops.object.mode_set(mode='OBJECT')
            for v in mesh.vertices:
                v.select = False
                for g in v.groups:
                    if g.group in group_indices:
                        v.select = True
                        break
            bpy.ops.object.mode_set(mode='EDIT')
            
            bpy.ops.mesh.separate(type='SELECTED')
            
            bpy.ops.object.mode_set(mode='OBJECT')
            new_obj = bpy.context.selected_objects[-1]
            new_obj.name = f"{obj.name}_{prefix}"
            separated_objects.append(new_obj)

        bpy.ops.object.mode_set(mode='OBJECT')
        
        separate_end = time.time()
        print(f"Time to separate mesh by vertex group prefix: {separate_end - separate_start} seconds")
        return separated_objects

    @staticmethod
    def combine_numeric_groups():
        numeric_objects = [obj for obj in bpy.data.objects if obj.type == 'MESH' and "numeric_groups" in obj.name]
        if numeric_objects:
            for obj in numeric_objects:
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj
            bpy.ops.object.join()
            combined_obj = bpy.context.active_object
            if combined_obj:
                combined_obj.name = "Numbers"

    @staticmethod
    def delete_empty_shapekeys(obj):
        if not obj.data.shape_keys:
            return
        key_blocks = obj.data.shape_keys.key_blocks
        empty_keys = [key for key in key_blocks if all(v.co == key.relative_key.data[i].co for i, v in enumerate(key.data))]
        for key in empty_keys:
            obj.shape_key_remove(key)

    @staticmethod
    def rename_mesh_based_on_vertex_groups(obj, base_collection):
        vertex_groups = obj.vertex_groups
        if not vertex_groups:
            return
        
        group_names = [vg.name for vg in vertex_groups]
        all_numeric = all(SplitMeshByVertexGroupsOperator.is_numeric(name.split('_')[0]) for name in group_names)
        
        if all_numeric:
            obj.name = f"{base_collection.name}Body"
        else:
            prefix = group_names[0].split('_')[0]
            obj.name = f"{prefix}"
        
        selected_obj = bpy.context.active_object
        if selected_obj and selected_obj.type == 'MESH':
            bpy.context.view_layer.objects.active = selected_obj
            selected_obj.select_set(True)
            separated_objects = SplitMeshByVertexGroupsOperator.separate_mesh_by_vertex_group_prefix(selected_obj)

            
            remove_start = time.time()
            bpy.data.objects.remove(selected_obj, do_unlink=True)
            bpy.ops.object.select_all(action='DESELECT')
            
            for obj in separated_objects:
                obj.select_set(True)
                SplitMeshByVertexGroupsOperator.remove_unused_vertex_groups(obj)
                SplitMeshByVertexGroupsOperator.rename_mesh_based_on_vertex_groups(obj, base_collection)
                SplitMeshByVertexGroupsOperator.delete_empty_shapekeys(obj)

            bpy.context.view_layer.objects.active = separated_objects[0] if separated_objects else None
            bpy.ops.object.mode_set(mode='OBJECT')
            remove_end = time.time()
            print(f"Time to process separated objects: {remove_end - remove_start} seconds")
            SplitMeshByVertexGroupsOperator.combine_numeric_groups()
            meshes = [obj for obj in bpy.data.objects if obj.type == 'MESH']
            bpy.ops.object.select_all(action='DESELECT')
            for mesh in meshes:
                mesh.select_set(True)
            bpy.context.view_layer.objects.active = meshes[0] if meshes else None

class ResetVertexGroupsNamesOperator(Operator):
    """Reset Vertex Groups Names by removing prefixes"""
    bl_idname = "object.reset_vertex_groups_names"
    bl_label = "Reset Vertex Groups Names"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.armature_matching_props
        base_collection = props.base_collection

        if not base_collection:
            self.report({'ERROR'}, "Base collection not found.")
            return {'CANCELLED'}

        base_objs = [obj for obj in base_collection.objects if obj.type == 'MESH']

        for obj in base_objs:
            for vg in obj.vertex_groups:
                new_name = vg.name.split('_')[-1]
                if new_name.isdigit():
                    vg.name = new_name

        self.report({'INFO'}, "Vertex groups names reset successfully.")
        return {'FINISHED'}
    
#MARK: PANEL  
class ArmatureXXMIPanel(Panel):
    bl_label = "ArmatureXXMI"
    bl_idname = "OBJECT_PT_armature_xxmi"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'XXMI Scripts'
    bl_options = {'DEFAULT_CLOSED'} 
    def draw(self, context):
        layout = self.layout
        props = context.scene.armature_matching_props

        box = layout.box()
        row = box.row()
        split = row.split(factor=0.7)
        col = split.column()
        col.label(text="Armature Matching", icon='FILE_REFRESH')
        col = split.column()
        col.alignment = 'RIGHT'
        col.label(text=f"v{bl_info['version'][0]}.{bl_info['version'][1]}")

        box.prop(props, "armature_mode")
        box.prop(props, "mode")  
        
        if props.mode == 'HONKAI':
            row = box.row(align=True)
            row.prop(props, "ignore_hair")
            row.prop(props, "ignore_head")
        
        box.prop(props, "base_collection")
        box.prop(props, "target_collection")
        box.prop(props, "armature", icon='ARMATURE_DATA')
        
        row = box.row(align=True)
        row.scale_y = 1.2
        row.operator("object.armature_matching", icon='CON_ARMATURE')

        layout.separator(factor=0.2)
  
        box = layout.box()
        box.label(text="Operations", icon='PREFERENCES')
        col = box.column(align=True)

        col.scale_y = 1.1
        
        col.operator("object.mirror_armature", icon='MOD_MIRROR')
        col.operator("object.clean_armature", icon='BRUSH_DATA')
        col.operator("object.setup_character_for_armature", icon='ARMATURE_DATA')
        col.operator("object.split_mesh_by_vertex_groups", icon='MESH_DATA')
        col.operator("object.reset_vertex_groups_names", icon='GROUP_VERTEX')

classes = [
    ArmatureMatchingProperties,
    ArmatureMatchingOperator,
    SetupCharacterForArmatureOperator,
    CleanArmatureOperator,
    MirrorArmatureOperator,
    SplitMeshByVertexGroupsOperator,
    ArmatureXXMIPanel,
    ResetVertexGroupsNamesOperator,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.armature_matching_props = PointerProperty(type=ArmatureMatchingProperties)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.armature_matching_props

if __name__ == "__main__":
    register()