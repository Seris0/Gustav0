#Author: Gustav0_

#Set up armature for certain anime games

# Main matching logic get from the gigachad Comilarex https://gamebanana.com/tools/15699

import bpy
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import PointerProperty, EnumProperty, BoolProperty
from mathutils import Vector


bl_info = {
    "name": "ArmatureXXMI",
    "author": "Gustav",
    "version": (2, 2),
    "blender": (3, 6, 2),
    "description": "Matches vertex groups based on weight paint centroids and surface area. Also can flip and pull weight from other objects.",
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
            ('GENSHIN', "Genshin Impact", "Process for Genshin Impact")
        ],
        default='HONKAI'
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

        print(f"Base Collection: {base_collection}")
        print(f"Target Collection: {target_collection}")
        print(f"Armature Object: {armature_obj}")
        print(f"Mode: {mode}")

        if base_collection and target_collection and armature_obj:
            if armature_obj.type == 'ARMATURE':
                print("Processing target collection...")
                target_obj = process_target_collection(target_collection)
                print("Processing base collection...")
                base_obj = process_base_collection(base_collection, mode, ignore_hair, ignore_head)
                
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

                    self.report({'INFO'}, f"Armature moved to base collection and renamed to {new_armature_name}.")
                else:
                    self.report({'ERROR'}, "Failed to process collections.")
            else:
                self.report({'ERROR'}, "Invalid object type for armature.")
        else:
            self.report({'ERROR'}, "One or more collections not found.")

        return {'FINISHED'}

def process_target_collection(collection):
    target_objs = [obj for obj in collection.objects if obj.type == 'MESH']
    
    for obj in target_objs:
        if 'weapon' in obj.name.lower() or 'face' in obj.name.lower():
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

def process_base_collection(collection, mode, ignore_hair, ignore_head):
    base_objs = [obj for obj in collection.objects if obj.type == 'MESH']
    
    if ignore_hair:
        print("Ignoring hair meshes...")
        base_objs = [obj for obj in base_objs if 'hair' not in obj.name.lower()]
    if ignore_head:
        print("Ignoring head meshes...")
        base_objs = [obj for obj in base_objs if 'head' not in obj.name.lower()]

    if mode == 'HONKAI':
        base_objs = [obj for obj in base_objs if 'face' not in obj.name.lower()]
        
        body_meshes = [obj for obj in base_objs if 'body' in obj.name.lower()]
        other_meshes = [obj for obj in base_objs if 'body' not in obj.name.lower()]
        
        if body_meshes:
            bpy.ops.object.select_all(action='DESELECT')
            for obj in body_meshes:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = body_meshes[0]
            bpy.ops.object.join()
            joined_body_mesh = bpy.context.view_layer.objects.active
            other_meshes.append(joined_body_mesh)
        base_objs = other_meshes
    
    for obj in base_objs:
        mesh_name = obj.name.split('-')[0]
        for vg in obj.vertex_groups:
            new_name = f"{mesh_name}_{vg.name}"
            vg.name = new_name
    
    bpy.ops.object.select_all(action='DESELECT')
    for obj in base_objs:
        obj.select_set(True)
    
    if len(base_objs) > 0:
        bpy.context.view_layer.objects.active = base_objs[0]
        bpy.ops.object.join()
        
        return bpy.context.view_layer.objects.active
    else:
        return None
    
def get_weighted_center(obj, vgroup):
    total_weight_area = 0.0
    weighted_position_sum = Vector((0.0, 0.0, 0.0))

    vertex_influence_area = calculate_vertex_influence_area(obj)

    for vertex in obj.data.vertices:
        weight = get_vertex_group_weight(vgroup, vertex)
        influence_area = vertex_influence_area[vertex.index]
        weight_area = weight * influence_area

        if weight_area > 0:
            weighted_position_sum += obj.matrix_world @ vertex.co * weight_area
            total_weight_area += weight_area

    if total_weight_area > 0:
        center = weighted_position_sum / total_weight_area
        print(f"Center for {vgroup.name}: {center}")
        return center
    else:
        print(f"No weighted center for {vgroup.name}")
        return None

def calculate_vertex_influence_area(obj):
    vertex_area = [0.0] * len(obj.data.vertices)
    
    for face in obj.data.polygons:
        area_per_vertex = face.area / len(face.vertices)
        for vert_idx in face.vertices:
            vertex_area[vert_idx] += area_per_vertex

    return vertex_area

def get_vertex_group_weight(vgroup, vertex):
    for group in vertex.groups:
        if group.group == vgroup.index:
            return group.weight
    return 0.0

def match_vertex_groups(base_obj, target_obj):
    matching_info = {}

    base_centers = {}
    for base_group in base_obj.vertex_groups:
        base_centers[base_group.name] = get_weighted_center(base_obj, base_group)

    for target_group in target_obj.vertex_groups:
        target_center = get_weighted_center(target_obj, target_group)
        if target_center is None:
            continue

        best_match = None
        best_distance = float('inf')

        for base_group_name, base_center in base_centers.items():
            if base_center is None:
                continue

            distance = (target_center - base_center).length
            if distance < best_distance:
                best_distance = distance
                best_match = base_group_name

        if best_match:
            print(f"Target group {target_group.name} matched with base group {best_match}")
            matching_info[target_group.name] = best_match

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
class SetupArmatureForCharacterOperator(Operator):
    """Setup Armature for Character"""
    bl_idname = "object.setup_armature_for_character"
    bl_label = "Setup Armature for Character"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.armature_matching_props
        armature_obj = props.armature
        
        if not armature_obj or armature_obj.type != 'ARMATURE':
            self.report({'ERROR'}, "A valid armature must be selected.")
            return {'CANCELLED'}
        
        bpy.context.view_layer.objects.active = armature_obj
        bpy.ops.object.mode_set(mode='EDIT')
        
        for bone in armature_obj.data.edit_bones:
            if "body" in bone.name.lower():
         
                number_part = ''.join(filter(str.isdigit, bone.name))
                bone.name = number_part
        
        bpy.ops.object.mode_set(mode='OBJECT')
        self.report({'INFO'}, "Setup Armature for Character executed.")
        return {'FINISHED'}

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

        print(f"Base Collection: {base_collection}")
        print(f"Mode: {mode}")
        print(f"Armature Mode: {armature_mode}")

        if base_collection:
            base_objs = [obj for obj in base_collection.objects if obj.type == 'MESH']

            if armature_mode == 'MERGED':
                if mode == 'GENSHIN':
                    bpy.ops.object.select_all(action='DESELECT')
                    for obj in base_objs:
                        obj.select_set(True)
                    bpy.context.view_layer.objects.active = base_objs[0]
                    bpy.ops.object.join()
                else:
                    body_meshes = [obj for obj in base_objs if 'body' in obj.name.lower()]
                    other_meshes = [obj for obj in base_objs if 'body' not in obj.name.lower()]

                    if body_meshes and mode in {'HONKAI', 'ZENLESS'}:
                        bpy.ops.object.select_all(action='DESELECT')
                        for obj in body_meshes:
                            obj.select_set(True)
                        bpy.context.view_layer.objects.active = body_meshes[0]
                        bpy.ops.object.join()
                        joined_body_mesh = bpy.context.view_layer.objects.active
                        other_meshes.append(joined_body_mesh)
                    base_objs = other_meshes

            if mode != 'GENSHIN':
                for obj in base_objs:
                    base_obj_name = obj.name.split('-')[0]
                    if 'body' not in obj.name.lower():
                        for vg in obj.vertex_groups:
                            if not vg.name.startswith(f"{base_obj_name}_"):
                                vg.name = f"{base_obj_name}_{vg.name}"

            self.report({'INFO'}, "Character set up for armature.")
        else:
            self.report({'ERROR'}, "Base collection not found.")

        return {'FINISHED'}
    
class CleanArmatureOperator(Operator):
    """Clean Armature Object by removing bones not linked to any vertex group"""
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


            bones_to_delete = [bone for bone in armature.edit_bones if bone.name not in vertex_group_names]
            print(f"Bones to delete: {bones_to_delete}")

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
        box.label(text="Armature Matching", icon='FILE_REFRESH')

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
        row.operator("object.armature_matching")
        

        layout.separator(factor=0.5)

        layout.operator("object.mirror_armature")
        layout.operator("object.clean_armature")
        layout.operator("object.setup_armature_for_character")
        layout.operator("object.setup_character_for_armature")


classes = [
    ArmatureMatchingProperties,
    ArmatureMatchingOperator,
    SetupArmatureForCharacterOperator,
    SetupCharacterForArmatureOperator,
    CleanArmatureOperator,
    MirrorArmatureOperator,
    ArmatureXXMIPanel,
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