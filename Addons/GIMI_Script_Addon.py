#Author: Gustav0
#Special thanks to Silent for providing several scripts and 3dframeanalyse, Murren for providing UV and Color and LeoTools for QuickImport.

import os
import re
import bpy
import io
import bmesh
from glob import glob
from array import array
import struct
import numpy
import itertools
import collections
import textwrap
import shutil
import webbrowser
from bpy.props import PointerProperty, StringProperty, EnumProperty
from bpy.types import Object, Operator, Panel, PropertyGroup
from mathutils import Vector
from bpy_extras.io_utils import unpack_list, ImportHelper, ExportHelper, axis_conversion
from bpy.props import BoolProperty, StringProperty, CollectionProperty
from blender_dds_addon import import_dds
from bpy.utils import register_class, unregister_class


bl_info = {
    "name": "Gimi Scripts",
    "author": "Gustav0",
    "version": (1, 0),
    "blender": (3, 6, 2),
    "description": "Script Compilation",
    "category": "Object",
}


try:
    # Blender 2.80:
    from bpy_extras.io_utils import orientation_helper
    IOOBJOrientationHelper = type('DummyIOOBJOrientationHelper', (object,), {})
except ImportError:
    # Blender 2.79:
    from bpy_extras.io_utils import orientation_helper_factory
    IOOBJOrientationHelper = orientation_helper_factory("IOOBJOrientationHelper", axis_forward='-Z', axis_up='Y')
    class orientation_helper:
        def __init__(self, **orientation_kwargs):
            pass
        def __call__(self, cls):
            return cls

if bpy.app.version >= (2, 80):
    import_menu = bpy.types.TOPBAR_MT_file_import
    export_menu = bpy.types.TOPBAR_MT_file_export
    vertex_color_layer_channels = 4
else:
    import_menu = bpy.types.INFO_MT_file_import
    export_menu = bpy.types.INFO_MT_file_export
    vertex_color_layer_channels = 3

def make_annotations(cls):
    """Converts class fields to annotations if running with Blender 2.8"""
    if bpy.app.version < (2, 80):
        return cls
    bl_props = {k: v for k, v in cls.__dict__.items() if isinstance(v, tuple)}
    if bl_props:
        if '__annotations__' not in cls.__dict__:
            setattr(cls, '__annotations__', {})
        annotations = cls.__dict__['__annotations__']
        for k, v in bl_props.items():
            annotations[k] = v
            delattr(cls, k)
    return cls

def select_get(object):
    """Multi version compatibility for getting object selection"""
    if hasattr(object, "select_get"):
        return object.select_get()
    else:
        return object.select

def select_set(object, state):
    """Multi version compatibility for setting object selection"""
    if hasattr(object, "select_set"):
        object.select_set(state)
    else:
        object.select = state

def hide_get(object):
    """Multi version compatibility for getting object hidden state"""
    if hasattr(object, "hide_get"):
        return object.hide_get()
    else:
        return object.hide

def hide_set(object, state):
    """Multi version compatibility for setting object hidden state"""
    if hasattr(object, "hide_set"):
        object.hide_set(state)
    else:
        object.hide = state

def set_active_object(context, obj):
    """Get the active object in a 2.7 and 2.8 compatible way"""
    if hasattr(context, "view_layer"):
        context.view_layer.objects.active = obj # the 2.8 way
    else:
        context.scene.objects.active = obj # the 2.7 way

def get_active_object(context):
    """Get the active object in a 2.7 and 2.8 compatible way"""
    if hasattr(context, "view_layer"):
        return context.view_layer.objects.active
    else:
        return context.scene.objects.active

def link_object_to_scene(context, obj):
    if hasattr(context.scene, "collection"): # Blender 2.80
        context.scene.collection.objects.link(obj)
    else: # Blender 2.79
        context.scene.objects.link(obj)

def unlink_object(context, obj):
    if hasattr(context.scene, "collection"): # Blender 2.80
        context.scene.collection.objects.unlink(obj)
    else: # Blender 2.79
        context.scene.objects.unlink(obj)

import operator # to get function names for operators like @, +, -
def matmul(a, b):
    """Perform matrix multiplication in a blender 2.7 and 2.8 safe way"""
    if hasattr(bpy.app, "version") and bpy.app.version >= (2, 80):
        return operator.matmul(a, b) # the same as writing a @ b
    else:
        return a * b

############## End Blender 2.7 / 2.8 compatibility wrappers ##############




def keys_to_ints(d):
    return {k.isdecimal() and int(k) or k:v for k,v in d.items()}
def keys_to_strings(d):
    return {str(k):v for k,v in d.items()}

class Fatal(Exception): pass

# TODO: Support more DXGI formats:
f32_pattern = re.compile(r'''(?:DXGI_FORMAT_)?(?:[RGBAD]32)+_FLOAT''')
f16_pattern = re.compile(r'''(?:DXGI_FORMAT_)?(?:[RGBAD]16)+_FLOAT''')
u32_pattern = re.compile(r'''(?:DXGI_FORMAT_)?(?:[RGBAD]32)+_UINT''')
u16_pattern = re.compile(r'''(?:DXGI_FORMAT_)?(?:[RGBAD]16)+_UINT''')
u8_pattern = re.compile(r'''(?:DXGI_FORMAT_)?(?:[RGBAD]8)+_UINT''')
s32_pattern = re.compile(r'''(?:DXGI_FORMAT_)?(?:[RGBAD]32)+_SINT''')
s16_pattern = re.compile(r'''(?:DXGI_FORMAT_)?(?:[RGBAD]16)+_SINT''')
s8_pattern = re.compile(r'''(?:DXGI_FORMAT_)?(?:[RGBAD]8)+_SINT''')
unorm16_pattern = re.compile(r'''(?:DXGI_FORMAT_)?(?:[RGBAD]16)+_UNORM''')
unorm8_pattern = re.compile(r'''(?:DXGI_FORMAT_)?(?:[RGBAD]8)+_UNORM''')
snorm16_pattern = re.compile(r'''(?:DXGI_FORMAT_)?(?:[RGBAD]16)+_SNORM''')
snorm8_pattern = re.compile(r'''(?:DXGI_FORMAT_)?(?:[RGBAD]8)+_SNORM''')

misc_float_pattern = re.compile(r'''(?:DXGI_FORMAT_)?(?:[RGBAD][0-9]+)+_(?:FLOAT|UNORM|SNORM)''')
misc_int_pattern = re.compile(r'''(?:DXGI_FORMAT_)?(?:[RGBAD][0-9]+)+_[SU]INT''')

def EncoderDecoder(fmt):
    if f32_pattern.match(fmt):
        return (lambda data: b''.join(struct.pack('<f', x) for x in data),
                lambda data: numpy.frombuffer(data, numpy.float32).tolist())
    if f16_pattern.match(fmt):
        return (lambda data: numpy.fromiter(data, numpy.float16).tobytes(),
                lambda data: numpy.frombuffer(data, numpy.float16).tolist())
    if u32_pattern.match(fmt):
        return (lambda data: numpy.fromiter(data, numpy.uint32).tobytes(),
                lambda data: numpy.frombuffer(data, numpy.uint32).tolist())
    if u16_pattern.match(fmt):
        return (lambda data: numpy.fromiter(data, numpy.uint16).tobytes(),
                lambda data: numpy.frombuffer(data, numpy.uint16).tolist())
    if u8_pattern.match(fmt):
        return (lambda data: numpy.fromiter(data, numpy.uint8).tobytes(),
                lambda data: numpy.frombuffer(data, numpy.uint8).tolist())
    if s32_pattern.match(fmt):
        return (lambda data: numpy.fromiter(data, numpy.int32).tobytes(),
                lambda data: numpy.frombuffer(data, numpy.int32).tolist())
    if s16_pattern.match(fmt):
        return (lambda data: numpy.fromiter(data, numpy.int16).tobytes(),
                lambda data: numpy.frombuffer(data, numpy.int16).tolist())
    if s8_pattern.match(fmt):
        return (lambda data: numpy.fromiter(data, numpy.int8).tobytes(),
                lambda data: numpy.frombuffer(data, numpy.int8).tolist())

    if unorm16_pattern.match(fmt):
        return (lambda data: numpy.around((numpy.fromiter(data, numpy.float32) * 65535.0)).astype(numpy.uint16).tobytes(),
                lambda data: (numpy.frombuffer(data, numpy.uint16) / 65535.0).tolist())
    if unorm8_pattern.match(fmt):
        return (lambda data: numpy.around((numpy.fromiter(data, numpy.float32) * 255.0)).astype(numpy.uint8).tobytes(),
                lambda data: (numpy.frombuffer(data, numpy.uint8) / 255.0).tolist())
    if snorm16_pattern.match(fmt):
        return (lambda data: numpy.around((numpy.fromiter(data, numpy.float32) * 32767.0)).astype(numpy.int16).tobytes(),
                lambda data: (numpy.frombuffer(data, numpy.int16) / 32767.0).tolist())
    if snorm8_pattern.match(fmt):
        return (lambda data: numpy.around((numpy.fromiter(data, numpy.float32) * 127.0)).astype(numpy.int8).tobytes(),
                lambda data: (numpy.frombuffer(data, numpy.int8) / 127.0).tolist())

    raise Fatal('File uses an unsupported DXGI Format: %s' % fmt)

components_pattern = re.compile(r'''(?<![0-9])[0-9]+(?![0-9])''')
def format_components(fmt):
    return len(components_pattern.findall(fmt))

def format_size(fmt):
    matches = components_pattern.findall(fmt)
    return sum(map(int, matches)) // 8

class InputLayoutElement(object):
    def __init__(self, arg):
        if isinstance(arg, io.IOBase):
            self.from_file(arg)
        else:
            self.from_dict(arg)

        self.encoder, self.decoder = EncoderDecoder(self.Format)

    def from_file(self, f):
        self.SemanticName = self.next_validate(f, 'SemanticName')
        self.SemanticIndex = int(self.next_validate(f, 'SemanticIndex'))
        self.Format = self.next_validate(f, 'Format')
        self.InputSlot = int(self.next_validate(f, 'InputSlot'))
        self.AlignedByteOffset = self.next_validate(f, 'AlignedByteOffset')
        if self.AlignedByteOffset == 'append':
            raise Fatal('Input layouts using "AlignedByteOffset=append" are not yet supported')
        self.AlignedByteOffset = int(self.AlignedByteOffset)
        self.InputSlotClass = self.next_validate(f, 'InputSlotClass')
        self.InstanceDataStepRate = int(self.next_validate(f, 'InstanceDataStepRate'))

    def to_dict(self):
        d = {}
        d['SemanticName'] = self.SemanticName
        d['SemanticIndex'] = self.SemanticIndex
        d['Format'] = self.Format
        d['InputSlot'] = self.InputSlot
        d['AlignedByteOffset'] = self.AlignedByteOffset
        d['InputSlotClass'] = self.InputSlotClass
        d['InstanceDataStepRate'] = self.InstanceDataStepRate
        return d

    def to_string(self, indent=2):
        return textwrap.indent(textwrap.dedent('''
            SemanticName: %s
            SemanticIndex: %i
            Format: %s
            InputSlot: %i
            AlignedByteOffset: %i
            InputSlotClass: %s
            InstanceDataStepRate: %i
        ''').lstrip() % (
            self.SemanticName,
            self.SemanticIndex,
            self.Format,
            self.InputSlot,
            self.AlignedByteOffset,
            self.InputSlotClass,
            self.InstanceDataStepRate,
        ), ' '*indent)

    def from_dict(self, d):
        self.SemanticName = d['SemanticName']
        self.SemanticIndex = d['SemanticIndex']
        self.Format = d['Format']
        self.InputSlot = d['InputSlot']
        self.AlignedByteOffset = d['AlignedByteOffset']
        self.InputSlotClass = d['InputSlotClass']
        self.InstanceDataStepRate = d['InstanceDataStepRate']

    @staticmethod
    def next_validate(f, field):
        line = next(f).strip()
        assert(line.startswith(field + ': '))
        return line[len(field) + 2:]

    @property
    def name(self):
        if self.SemanticIndex:
            return '%s%i' % (self.SemanticName, self.SemanticIndex)
        return self.SemanticName

    def pad(self, data, val):
        padding = format_components(self.Format) - len(data)
        assert(padding >= 0)
        return data + [val]*padding

    def clip(self, data):
        return data[:format_components(self.Format)]

    def size(self):
        return format_size(self.Format)

    def is_float(self):
        return misc_float_pattern.match(self.Format)

    def is_int(self):
        return misc_int_pattern.match(self.Format)

    def encode(self, data):
        # print(self.Format, data)
        return self.encoder(data)

    def decode(self, data):
        return self.decoder(data)

    def __eq__(self, other):
        return \
            self.SemanticName == other.SemanticName and \
            self.SemanticIndex == other.SemanticIndex and \
            self.Format == other.Format and \
            self.InputSlot == other.InputSlot and \
            self.AlignedByteOffset == other.AlignedByteOffset and \
            self.InputSlotClass == other.InputSlotClass and \
            self.InstanceDataStepRate == other.InstanceDataStepRate

class InputLayout(object):
    def __init__(self, custom_prop=[], stride=0):
        self.elems = collections.OrderedDict()
        self.stride = stride
        for item in custom_prop:
            elem = InputLayoutElement(item)
            self.elems[elem.name] = elem

    def serialise(self):
        return [x.to_dict() for x in self.elems.values()]

    def to_string(self):
        ret = ''
        for i, elem in enumerate(self.elems.values()):
            ret += 'element[%i]:\n' % i
            ret += elem.to_string()
        return ret

    def parse_element(self, f):
        elem = InputLayoutElement(f)
        self.elems[elem.name] = elem

    def __iter__(self):
        return iter(self.elems.values())

    def __getitem__(self, semantic):
        return self.elems[semantic]

    def encode(self, vertex):
        buf = bytearray(self.stride)

        for semantic, data in vertex.items():
            if semantic.startswith('~'):
                continue
            elem = self.elems[semantic]
            data = elem.encode(data)
            buf[elem.AlignedByteOffset:elem.AlignedByteOffset + len(data)] = data

        assert(len(buf) == self.stride)
        return buf

    def decode(self, buf):
        vertex = {}
        for elem in self.elems.values():
            data = buf[elem.AlignedByteOffset:elem.AlignedByteOffset + elem.size()]
            vertex[elem.name] = elem.decode(data)
        return vertex

    def __eq__(self, other):
        return self.elems == other.elems

class HashableVertex(dict):
    def __hash__(self):
        # Convert keys and values into immutable types that can be hashed
        immutable = tuple((k, tuple(v)) for k,v in sorted(self.items()))
        return hash(immutable)

class VertexBuffer(object):
    vb_elem_pattern = re.compile(r'''vb\d+\[\d*\]\+\d+ (?P<semantic>[^:]+): (?P<data>.*)$''')

    # Python gotcha - do not set layout=InputLayout() in the default function
    # parameters, as they would all share the *same* InputLayout since the
    # default values are only evaluated once on file load
    def __init__(self, f=None, layout=None, load_vertices=True):
        self.vertices = []
        self.layout = layout and layout or InputLayout()
        self.first = 0
        self.vertex_count = 0
        self.offset = 0
        self.topology = 'trianglelist'

        if f is not None:
            self.parse_vb_txt(f, load_vertices)

    def parse_vb_txt(self, f, load_vertices):
        for line in map(str.strip, f):
            # print(line)
            if line.startswith('byte offset:'):
                self.offset = int(line[13:])
            if line.startswith('first vertex:'):
                self.first = int(line[14:])
            if line.startswith('vertex count:'):
                self.vertex_count = int(line[14:])
            if line.startswith('stride:'):
                self.layout.stride = int(line[7:])
            if line.startswith('element['):
                self.layout.parse_element(f)
            if line.startswith('topology:'):
                self.topology = line[10:]
                if line != 'topology: trianglelist':
                    raise Fatal('"%s" is not yet supported' % line)
            if line.startswith('vertex-data:'):
                if not load_vertices:
                    return
                self.parse_vertex_data(f)
        assert(len(self.vertices) == self.vertex_count)

    def parse_vb_bin(self, f):
        f.seek(self.offset)
        # XXX: Should we respect the first/base vertex?
        # f.seek(self.first * self.layout.stride, whence=1)
        self.first = 0
        while True:
            vertex = f.read(self.layout.stride)
            if not vertex:
                break
            self.vertices.append(self.layout.decode(vertex))
        # We intentionally disregard the vertex count when loading from a
        # binary file, as we assume frame analysis might have only dumped a
        # partial buffer to the .txt files (e.g. if this was from a dump where
        # the draw call index count was overridden it may be cut short, or
        # where the .txt files contain only sub-meshes from each draw call and
        # we are loading the .buf file because it contains the entire mesh):
        self.vertex_count = len(self.vertices)

    def append(self, vertex):
        self.vertices.append(vertex)
        self.vertex_count += 1

    def parse_vertex_data(self, f):
        vertex = {}
        for line in map(str.strip, f):
            #print(line)
            if line.startswith('instance-data:'):
                break

            match = self.vb_elem_pattern.match(line)
            if match:
                vertex[match.group('semantic')] = self.parse_vertex_element(match)
            elif line == '' and vertex:
                self.vertices.append(vertex)
                vertex = {}
        if vertex:
            self.vertices.append(vertex)

    def parse_vertex_element(self, match):
        fields = match.group('data').split(',')

        if self.layout[match.group('semantic')].Format.endswith('INT'):
            return tuple(map(int, fields))

        return tuple(map(float, fields))

    def remap_blendindices(self, obj, mapping):
        def lookup_vgmap(x):
            vgname = obj.vertex_groups[x].name
            return mapping.get(vgname, mapping.get(x, x))

        for vertex in self.vertices:
            for semantic in list(vertex):
                if semantic.startswith('BLENDINDICES'):
                    vertex['~' + semantic] = vertex[semantic]
                    vertex[semantic] = tuple(lookup_vgmap(x) for x in vertex[semantic])

    def revert_blendindices_remap(self):
        # Significantly faster than doing a deep copy
        for vertex in self.vertices:
            for semantic in list(vertex):
                if semantic.startswith('BLENDINDICES'):
                    vertex[semantic] = vertex['~' + semantic]
                    del vertex['~' + semantic]

    def disable_blendweights(self):
        for vertex in self.vertices:
            for semantic in list(vertex):
                if semantic.startswith('BLENDINDICES'):
                    vertex[semantic] = (0, 0, 0, 0)

    def write(self, output, operator=None):
        for vertex in self.vertices:
            output.write(self.layout.encode(vertex))

        msg = 'Wrote %i vertices to %s' % (len(self), output.name)
        if operator:
            operator.report({'INFO'}, msg)
        else:
            print(msg)

    def __len__(self):
        return len(self.vertices)

    def merge(self, other):
        if self.layout != other.layout:
            raise Fatal('Vertex buffers have different input layouts - ensure you are only trying to merge the same vertex buffer split across multiple draw calls')
        if self.first != other.first:
            # FIXME: Future 3DMigoto might automatically set first from the
            # index buffer and chop off unreferenced vertices to save space
            raise Fatal('Cannot merge multiple vertex buffers - please check for updates of the 3DMigoto import script, or import each buffer separately')
        self.vertices.extend(other.vertices[self.vertex_count:])
        self.vertex_count = max(self.vertex_count, other.vertex_count)
        assert(len(self.vertices) == self.vertex_count)

    def wipe_semantic_for_testing(self, semantic, val=0):
        print('WARNING: WIPING %s FOR TESTING PURPOSES!!!' % semantic)
        semantic, _, components = semantic.partition('.')
        if components:
            components = [{'x':0, 'y':1, 'z':2, 'w':3}[c] for c in components]
        else:
            components = range(4)
        for vertex in self.vertices:
            for s in list(vertex):
                if s == semantic:
                    v = list(vertex[semantic])
                    for component in components:
                        if component < len(v):
                            v[component] = val
                    vertex[semantic] = v

class IndexBuffer(object):
    def __init__(self, *args, load_indices=True):
        self.faces = []
        self.first = 0
        self.index_count = 0
        self.format = 'DXGI_FORMAT_UNKNOWN'
        self.offset = 0
        self.topology = 'trianglelist'

        if isinstance(args[0], io.IOBase):
            assert(len(args) == 1)
            self.parse_ib_txt(args[0], load_indices)
        else:
            self.format, = args

        self.encoder, self.decoder = EncoderDecoder(self.format)

    def append(self, face):
        self.faces.append(face)
        self.index_count += len(face)

    def parse_ib_txt(self, f, load_indices):
        for line in map(str.strip, f):
            if line.startswith('byte offset:'):
                self.offset = int(line[13:])
            if line.startswith('first index:'):
                self.first = int(line[13:])
            elif line.startswith('index count:'):
                self.index_count = int(line[13:])
            elif line.startswith('topology:'):
                self.topology = line[10:]
                if line != 'topology: trianglelist':
                    raise Fatal('"%s" is not yet supported' % line)
            elif line.startswith('format:'):
                self.format = line[8:]
            elif line == '':
                if not load_indices:
                    return
                self.parse_index_data(f)
        assert(len(self.faces) * 3 == self.index_count)

    def parse_ib_bin(self, f):
        f.seek(self.offset)
        stride = format_size(self.format)
        # XXX: Should we respect the first index?
        # f.seek(self.first * stride, whence=1)
        self.first = 0

        face = []
        while True:
            index = f.read(stride)
            if not index:
                break
            face.append(*self.decoder(index))
            if len(face) == 3:
                self.faces.append(tuple(face))
                face = []
        assert(len(face) == 0)

        # we are loading the .buf file because it contains the entire mesh):
        self.index_count = len(self.faces) * 3

    def parse_index_data(self, f):
        for line in map(str.strip, f):
            face = tuple(map(int, line.split()))
            assert(len(face) == 3)
            self.faces.append(face)

    def merge(self, other):
        if self.format != other.format:
            raise Fatal('Index buffers have different formats - ensure you are only trying to merge the same index buffer split across multiple draw calls')
        self.first = min(self.first, other.first)
        self.index_count += other.index_count
        self.faces.extend(other.faces)

    def write(self, output, operator=None):
        for face in self.faces:
            output.write(self.encoder(face))

        msg = 'Wrote %i indices to %s' % (len(self), output.name)
        if operator:
            operator.report({'INFO'}, msg)
        else:
            print(msg)

    def __len__(self):
        return len(self.faces) * 3

def load_3dmigoto_mesh_bin(operator, vb_paths, ib_paths, pose_path):
    if len(vb_paths) != 1 or len(ib_paths) > 1:
        raise Fatal('Cannot merge meshes loaded from binary files')

    # Loading from binary files, but still need to use the .txt files as a
    # reference for the format:
    vb_bin_path, vb_txt_path = vb_paths[0]
    ib_bin_path, ib_txt_path = ib_paths[0]

    vb = VertexBuffer(open(vb_txt_path, 'r'), load_vertices=False)
    vb.parse_vb_bin(open(vb_bin_path, 'rb'))

    ib = None
    if ib_paths:
        ib = IndexBuffer(open(ib_txt_path, 'r'), load_indices=False)
        ib.parse_ib_bin(open(ib_bin_path, 'rb'))

    return vb, ib, os.path.basename(vb_bin_path), pose_path

def load_3dmigoto_mesh(operator, paths):
    vb_paths, ib_paths, use_bin, pose_path = zip(*paths)
    pose_path = pose_path[0]

    if use_bin[0]:
        return load_3dmigoto_mesh_bin(operator, vb_paths, ib_paths, pose_path)

    vb = VertexBuffer(open(vb_paths[0], 'r'))
    # Merge additional vertex buffers for meshes split over multiple draw calls:
    for vb_path in vb_paths[1:]:
        tmp = VertexBuffer(open(vb_path, 'r'))
        vb.merge(tmp)



    ib = None
    if ib_paths:
        ib = IndexBuffer(open(ib_paths[0], 'r'))
        # Merge additional vertex buffers for meshes split over multiple draw calls:
        for ib_path in ib_paths[1:]:
            tmp = IndexBuffer(open(ib_path, 'r'))
            ib.merge(tmp)

    return vb, ib, os.path.basename(vb_paths[0]), pose_path

def import_normals_step1(mesh, data):
    # Ensure normals are 3-dimensional:
    # XXX: Assertion triggers in DOA6
    if len(data[0]) == 4:
        if [x[3] for x in data] != [0.0]*len(data):
            raise Fatal('Normals are 4D')
    normals = [(x[0], x[1], x[2]) for x in data]

    #       we can only set custom lnors *after* calling it.
    mesh.create_normals_split()
    for l in mesh.loops:
        l.normal[:] = normals[l.vertex_index]

def import_normals_step2(mesh):
    # Taken from import_obj/import_fbx
    clnors = array('f', [0.0] * (len(mesh.loops) * 3))
    mesh.loops.foreach_get("normal", clnors)

    # Not sure this is still required with use_auto_smooth, but the other
    # importers do it, and at the very least it shouldn't hurt...
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))

    mesh.normals_split_custom_set(tuple(zip(*(iter(clnors),) * 3)))
    mesh.use_auto_smooth = True # This has a double meaning, one of which is to use the custom normals
    # XXX CHECKME: show_edge_sharp moved in 2.80, but I can't actually
    # recall what it does and have a feeling it was unimportant:
    #mesh.show_edge_sharp = True

def import_vertex_groups(mesh, obj, blend_indices, blend_weights):
    assert(len(blend_indices) == len(blend_weights))
    if blend_indices:
        # We will need to make sure we re-export the same blend indices later -
        # that they haven't been renumbered. Not positive whether it is better
        # to use the vertex group index, vertex group name or attach some extra
        # data. Make sure the indices and names match:
        num_vertex_groups = max(itertools.chain(*itertools.chain(*blend_indices.values()))) + 1
        for i in range(num_vertex_groups):
            obj.vertex_groups.new(name=str(i))
        for vertex in mesh.vertices:
            for semantic_index in sorted(blend_indices.keys()):
                for i, w in zip(blend_indices[semantic_index][vertex.index], blend_weights[semantic_index][vertex.index]):
                    if w == 0.0:
                        continue
                    obj.vertex_groups[i].add((vertex.index,), w, 'REPLACE')
def import_uv_layers(mesh, obj, texcoords, flip_texcoord_v):
    for (texcoord, data) in sorted(texcoords.items()):
        # TEXCOORDS can have up to four components, but UVs can only have two
        # dimensions. Not positive of the best way to handle this in general,
        # but for now I'm thinking that splitting the TEXCOORD into two sets of
        # UV coordinates might work:
        dim = len(data[0])
        if dim == 4:
            components_list = ('xy', 'zw')
        elif dim == 2:
            components_list = ('xy',)
        else:
            raise Fatal('Unhandled TEXCOORD dimension: %i' % dim)
        cmap = {'x': 0, 'y': 1, 'z': 2, 'w': 3}

        for components in components_list:
            uv_name = 'TEXCOORD%s.%s' % (texcoord and texcoord or '', components)
            if hasattr(mesh, 'uv_textures'): # 2.79
                mesh.uv_textures.new(uv_name)
            else: # 2.80
                mesh.uv_layers.new(name=uv_name)
            blender_uvs = mesh.uv_layers[uv_name]

            # This will assign a texture to the UV layer, which works fine but
            # working out which texture maps to which UV layer is guesswork
            # before the import and the artist may as well just assign it
            # themselves in the UV editor pane when they can see the unwrapped
            # mesh to compare it with the dumped textures:
            #
            #path = textures.get(uv_layer, None)
            #if path is not None:
            #    image = load_image(path)
            #    for i in range(len(mesh.polygons)):
            #        mesh.uv_textures[uv_layer].data[i].image = image

            # Can't find an easy way to flip the display of V in Blender, so
            # add an option to flip it on import & export:
            if flip_texcoord_v:
                flip_uv = lambda uv: (uv[0], 1.0 - uv[1])
                # Record that V was flipped so we know to undo it when exporting:
                obj['3DMigoto:' + uv_name] = {'flip_v': True}
            else:
                flip_uv = lambda uv: uv

            uvs = [[d[cmap[c]] for c in components] for d in data]
            for l in mesh.loops:
                blender_uvs.data[l.index].uv = flip_uv(uvs[l.vertex_index])

# This loads unknown data from the vertex buffers as vertex layers
def import_vertex_layers(mesh, obj, vertex_layers):
    for (element_name, data) in sorted(vertex_layers.items()):
        dim = len(data[0])
        cmap = {0: 'x', 1: 'y', 2: 'z', 3: 'w'}
        for component in range(dim):

            if dim != 1 or element_name.find('.') == -1:
                layer_name = '%s.%s' % (element_name, cmap[component])
            else:
                layer_name = element_name

            if type(data[0][0]) == int:
                mesh.vertex_layers_int.new(name=layer_name)
                layer = mesh.vertex_layers_int[layer_name]
                for v in mesh.vertices:
                    val = data[v.index][component]
                    # Blender integer layers are 32bit signed and will throw an
                    # exception if we are assigning an unsigned value that
                    # can't fit in that range. Reinterpret as signed if necessary:
                    if val < 0x80000000:
                        layer.data[v.index].value = val
                    else:
                        layer.data[v.index].value = struct.unpack('i', struct.pack('I', val))[0]
            elif type(data[0][0]) == float:
                mesh.vertex_layers_float.new(name=layer_name)
                layer = mesh.vertex_layers_float[layer_name]
                for v in mesh.vertices:
                    layer.data[v.index].value = data[v.index][component]
            else:
                raise Fatal('BUG: Bad layer type %s' % type(data[0][0]))

def import_faces_from_ib(mesh, ib):
    mesh.loops.add(len(ib.faces) * 3)
    mesh.polygons.add(len(ib.faces))
    mesh.loops.foreach_set('vertex_index', unpack_list(ib.faces))
    mesh.polygons.foreach_set('loop_start', [x*3 for x in range(len(ib.faces))])
    mesh.polygons.foreach_set('loop_total', [3] * len(ib.faces))

def import_faces_from_vb(mesh, vb):
    # Only lightly tested
    num_faces = len(vb.vertices) // 3
    mesh.loops.add(num_faces * 3)
    mesh.polygons.add(num_faces)
    mesh.loops.foreach_set('vertex_index', [x for x in range(num_faces * 3)])
    mesh.polygons.foreach_set('loop_start', [x*3 for x in range(num_faces)])
    mesh.polygons.foreach_set('loop_total', [3] * num_faces)

def import_vertices(mesh, vb):
    mesh.vertices.add(len(vb.vertices))

    seen_offsets = set()
    blend_indices = {}
    blend_weights = {}
    texcoords = {}
    vertex_layers = {}
    use_normals = False

    for elem in vb.layout:
        if elem.InputSlotClass != 'per-vertex':
            continue

        # TODO: Allow poorly named semantics to map to other meanings to be
        # properly interpreted. This still needs to be added to the GUI, and
        # mapped back on export. Alternatively, you can alter the input
        # assembler layout format in the vb*.txt / *.fmt files prior to import.
        semantic_translations = {
            #'ATTRIBUTE': 'POSITION', # UE4
        }
        translated_elem_name = semantic_translations.get(elem.name, elem.name)

        # Discard elements that reuse offsets in the vertex buffer, e.g. COLOR
        # and some TEXCOORDs may be aliases of POSITION:
        if (elem.InputSlot, elem.AlignedByteOffset) in seen_offsets:
            assert(translated_elem_name != 'POSITION')
            continue
        seen_offsets.add((elem.InputSlot, elem.AlignedByteOffset))

        data = tuple( x[elem.name] for x in vb.vertices )
        if translated_elem_name == 'POSITION':
            # Ensure positions are 3-dimensional:
            if len(data[0]) == 4:
                if ([x[3] for x in data] != [1.0]*len(data)):
                    # XXX: Leaving this fatal error in for now, as the meshes
                    # it triggers on in DOA6 (skirts) lie about almost every
                    # semantic and we cannot import them with this version of
                    # the script regardless. Comment it out if you want to try
                    # importing anyway and preserving the W coordinate in a
                    # vertex group. It might also be possible to project this
                    # back into 3D if we assume the coordinates are homogeneous
                    # (i.e. divide XYZ by W), but that might be assuming too
                    # much for a generic script.
                    raise Fatal('Positions are 4D')
                    # Occurs in some meshes in DOA6, such as skirts.
                    # W coordinate must be preserved in these cases.
                    print('Positions are 4D, storing W coordinate in POSITION.w vertex layer')
                    vertex_layers['POSITION.w'] = [[x[3]] for x in data]
            positions = [(x[0], x[1], x[2]) for x in data]
            mesh.vertices.foreach_set('co', unpack_list(positions))
        elif translated_elem_name.startswith('COLOR'):
            if len(data[0]) <= 3 or vertex_color_layer_channels == 4:
                # Either a monochrome/RGB layer, or Blender 2.80 which uses 4
                # channel layers
                mesh.vertex_colors.new(name=elem.name)
                color_layer = mesh.vertex_colors[elem.name].data
                c = vertex_color_layer_channels
                for l in mesh.loops:
                    color_layer[l.index].color = list(data[l.vertex_index]) + [0]*(c-len(data[l.vertex_index]))
            else:
                mesh.vertex_colors.new(name=elem.name + '.RGB')
                mesh.vertex_colors.new(name=elem.name + '.A')
                color_layer = mesh.vertex_colors[elem.name + '.RGB'].data
                alpha_layer = mesh.vertex_colors[elem.name + '.A'].data
                for l in mesh.loops:
                    color_layer[l.index].color = data[l.vertex_index][:3]
                    alpha_layer[l.index].color = [data[l.vertex_index][3], 0, 0]
        elif translated_elem_name == 'NORMAL':
            use_normals = True
            import_normals_step1(mesh, data)
        elif translated_elem_name in ('TANGENT', 'BINORMAL'):
        #    # XXX: loops.tangent is read only. Not positive how to handle
        #    # this, or if we should just calculate it when re-exporting.
        #    for l in mesh.loops:
        #        assert(data[l.vertex_index][3] in (1.0, -1.0))
        #        l.tangent[:] = data[l.vertex_index][0:3]
            print('NOTICE: Skipping import of %s in favour of recalculating on export' % elem.name)
        elif translated_elem_name.startswith('BLENDINDICES'):
            blend_indices[elem.SemanticIndex] = data
        elif translated_elem_name.startswith('BLENDWEIGHT'):
            blend_weights[elem.SemanticIndex] = data
        elif translated_elem_name.startswith('TEXCOORD') and elem.is_float():
            texcoords[elem.SemanticIndex] = data
        else:
            print('NOTICE: Storing unhandled semantic %s %s as vertex layer' % (elem.name, elem.Format))
            vertex_layers[elem.name] = data

    return (blend_indices, blend_weights, texcoords, vertex_layers, use_normals)

def import_3dmigoto(operator, context, paths, merge_meshes=True, **kwargs):
    if merge_meshes:
        return import_3dmigoto_vb_ib(operator, context, paths, **kwargs)
    else:
        obj = []
        for p in paths:
            try:
                obj.append(import_3dmigoto_vb_ib(operator, context, [p], **kwargs))
            except Fatal as e:
                operator.report({'ERROR'}, str(e) + ': ' + str(p[:2]))
        # FIXME: Group objects together
        return obj

def import_3dmigoto_vb_ib(operator, context, paths, flip_texcoord_v=True, axis_forward='-Z', axis_up='Y', pose_cb_off=[0,0], pose_cb_step=1):
    vb, ib, name, pose_path = load_3dmigoto_mesh(operator, paths)

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(mesh.name, mesh)

    global_matrix = axis_conversion(from_forward=axis_forward, from_up=axis_up).to_4x4()
    obj.matrix_world = global_matrix

    # Attach the vertex buffer layout to the object for later exporting. Can't
    # seem to retrieve this if attached to the mesh - to_mesh() doesn't copy it:
    obj['3DMigoto:VBLayout'] = vb.layout.serialise()
    obj['3DMigoto:VBStride'] = vb.layout.stride # FIXME: Strides of multiple vertex buffers
    obj['3DMigoto:FirstVertex'] = vb.first

    if ib is not None:
        import_faces_from_ib(mesh, ib)
        # Attach the index buffer layout to the object for later exporting.
        if ib.format == "DXGI_FORMAT_R16_UINT":
            obj['3DMigoto:IBFormat'] = "DXGI_FORMAT_R32_UINT"
        else:
            obj['3DMigoto:IBFormat'] = ib.format
        obj['3DMigoto:FirstIndex'] = ib.first
    else:
        import_faces_from_vb(mesh, vb)

    (blend_indices, blend_weights, texcoords, vertex_layers, use_normals) = import_vertices(mesh, vb)

    import_uv_layers(mesh, obj, texcoords, flip_texcoord_v)

    import_vertex_layers(mesh, obj, vertex_layers)

    import_vertex_groups(mesh, obj, blend_indices, blend_weights)

    # Validate closes the loops so they don't disappear after edit mode and probably other important things:
    mesh.validate(verbose=False, clean_customdata=False)  # *Very* important to not remove lnors here!
    # Not actually sure update is necessary. It seems to update the vertex normals, not sure what else:
    mesh.update()

    # Must be done after validate step:
    if use_normals:
        import_normals_step2(mesh)
    else:
        mesh.calc_normals()

    link_object_to_scene(context, obj)
    select_set(obj, True)
    set_active_object(context, obj)

    if pose_path is not None:
        import_pose(operator, context, pose_path, limit_bones_to_vertex_groups=True,
                axis_forward=axis_forward, axis_up=axis_up,
                pose_cb_off=pose_cb_off, pose_cb_step=pose_cb_step)
        set_active_object(context, obj)

    return obj

# from export_obj:
def mesh_triangulate(me):
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()

def blender_vertex_to_3dmigoto_vertex(mesh, obj, blender_loop_vertex, layout, texcoords):
    blender_vertex = mesh.vertices[blender_loop_vertex.vertex_index]
    pos = list(blender_vertex.undeformed_co)
    vertex = {}
    seen_offsets = set()

    # TODO: Warn if vertex is in too many vertex groups for this layout,
    # ignoring groups with weight=0.0
    vertex_groups = sorted(blender_vertex.groups, key=lambda x: x.weight, reverse=True)

    for elem in layout:
        if elem.InputSlotClass != 'per-vertex':
            continue

        if (elem.InputSlot, elem.AlignedByteOffset) in seen_offsets:
            continue
        seen_offsets.add((elem.InputSlot, elem.AlignedByteOffset))

        if elem.name == 'POSITION':
            if 'POSITION.w' in mesh.vertex_layers_float:
                vertex[elem.name] = pos + [mesh.vertex_layers_float['POSITION.w'].data[blender_loop_vertex.vertex_index].value]
            else:
                vertex[elem.name] = elem.pad(pos, 1.0)
        elif elem.name.startswith('COLOR'):
            if elem.name in mesh.vertex_colors:
                vertex[elem.name] = elem.clip(list(mesh.vertex_colors[elem.name].data[blender_loop_vertex.index].color))
            else:
                try:
                    vertex[elem.name] = list(mesh.vertex_colors[elem.name+'.RGB'].data[blender_loop_vertex.index].color)[:3] + \
                                            [mesh.vertex_colors[elem.name+'.A'].data[blender_loop_vertex.index].color[0]]
                except KeyError:
                    raise Fatal("ERROR: Unable to find COLOR property. Ensure the model you are exporting has a color attribute (of type Face Corner/Byte Color) called COLOR")
        elif elem.name == 'NORMAL':
            vertex[elem.name] = elem.pad(list(blender_loop_vertex.normal), 0.0)
        elif elem.name.startswith('TANGENT'):
            # DOAXVV has +1/-1 in the 4th component. Not positive what this is,
            # but guessing maybe the bitangent sign? Not even sure it is used...
            # FIXME: Other games
                #temporarily set tangent to normal for Anime Game since blender doesnt wanna import tangent
            vertex[elem.name] = elem.pad(list(blender_loop_vertex.normal), blender_loop_vertex.bitangent_sign)
        elif elem.name.startswith('BINORMAL'):
            # Some DOA6 meshes (skirts) use BINORMAL, but I'm not certain it is
            # actually the binormal. These meshes are weird though, since they
            # use 4 dimensional positions and normals, so they aren't something
            # we can really deal with at all. Therefore, the below is untested,
            # FIXME: So find a mesh where this is actually the binormal,
            # uncomment the below code and test.
            # normal = blender_loop_vertex.normal
            # tangent = blender_loop_vertex.tangent
            # binormal = numpy.cross(normal, tangent)
            # XXX: Does the binormal need to be normalised to a unit vector?
            # binormal = binormal / numpy.linalg.norm(binormal)
            # vertex[elem.name] = elem.pad(list(binormal), 0.0)
            pass
        elif elem.name.startswith('BLENDINDICES'):
            i = elem.SemanticIndex * 4
            vertex[elem.name] = elem.pad([ x.group for x in vertex_groups[i:i+4] ], 0)
        elif elem.name.startswith('BLENDWEIGHT'):
            # TODO: Warn if vertex is in too many vertex groups for this layout
            i = elem.SemanticIndex * 4
            vertex[elem.name] = elem.pad([ x.weight for x in vertex_groups[i:i+4] ], 0.0)
        elif elem.name.startswith('TEXCOORD') and elem.is_float():
            # FIXME: Handle texcoords of other dimensions
            uvs = []
            for uv_name in ('%s.xy' % elem.name, '%s.zw' % elem.name):
                if uv_name in texcoords:
                    uvs += list(texcoords[uv_name][blender_loop_vertex.index])

            vertex[elem.name] = uvs
        else:
            # Unhandled semantics are saved in vertex layers
            data = []
            for component in 'xyzw':
                layer_name = '%s.%s' % (elem.name, component)
                if layer_name in mesh.vertex_layers_int:
                    data.append(mesh.vertex_layers_int[layer_name].data[blender_loop_vertex.vertex_index].value)
                elif layer_name in mesh.vertex_layers_float:
                    data.append(mesh.vertex_layers_float[layer_name].data[blender_loop_vertex.vertex_index].value)
            if data:
                #print('Retrieved unhandled semantic %s %s from vertex layer' % (elem.name, elem.Format), data)
                vertex[elem.name] = data

        if elem.name not in vertex:
            print('NOTICE: Unhandled vertex element: %s' % elem.name)
        #else:
        #    print('%s: %s' % (elem.name, repr(vertex[elem.name])))

    return vertex

def unit_vector(vector):
    a = numpy.linalg.norm(vector, axis=max(len(vector.shape)-1,0), keepdims=True)
    return numpy.divide(vector, a, out=numpy.zeros_like(vector), where= a!=0)

def antiparallel_search(ConnectedFaceNormals):
    a = numpy.einsum('ij,kj->ik', ConnectedFaceNormals, ConnectedFaceNormals)
    return numpy.any((a>-1.000001)&(a<-0.999999))

def precision(x): 
    return -int(numpy.floor(numpy.log10(x)))

def recursive_connections(Over2_connected_points):
    for entry, connectedpointentry in Over2_connected_points.items():
        if len(connectedpointentry & Over2_connected_points.keys()) < 2:
            Over2_connected_points.pop(entry)
            if len(Over2_connected_points) < 3:
                return False
            return recursive_connections(Over2_connected_points)
    return True
    
def checkEnclosedFacesVertex(ConnectedFaces, vg_set, Precalculated_Outline_data):
    
    Main_connected_points = {}
        # connected points non-same vertex
    for face in ConnectedFaces:
        non_vg_points = [p for p in face if p not in vg_set]
        if len(non_vg_points) > 1:
            for point in non_vg_points:
                Main_connected_points.setdefault(point, []).extend([x for x in non_vg_points if x != point])
        # connected points same vertex
    New_Main_connect = {}
    for entry, value in Main_connected_points.items():
        for val in value:
            ivspv = Precalculated_Outline_data.get('Same_Vertex').get(val)-{val}
            intersect_sidevertex = ivspv & Main_connected_points.keys()
            if intersect_sidevertex:
                New_Main_connect.setdefault(entry, []).extend(list(intersect_sidevertex))
        # connected points same vertex reverse connection
    for key, value in New_Main_connect.items():
        Main_connected_points.get(key).extend(value)
        for val in value:
            Main_connected_points.get(val).append(key)
        # exclude for only 2 way paths 
    Over2_connected_points = {k: set(v) for k, v in Main_connected_points.items() if len(v) > 1}

    return recursive_connections(Over2_connected_points)

def blender_vertex_to_3dmigoto_vertex_outline(mesh, obj, blender_loop_vertex, layout, texcoords, export_Outline):
    blender_vertex = mesh.vertices[blender_loop_vertex.vertex_index]
    pos = list(blender_vertex.undeformed_co)
    blp_normal = list(blender_loop_vertex.normal)
    vertex = {}
    seen_offsets = set()

    # TODO: Warn if vertex is in too many vertex groups for this layout,
    # ignoring groups with weight=0.0
    vertex_groups = sorted(blender_vertex.groups, key=lambda x: x.weight, reverse=True)

    for elem in layout:
        if elem.InputSlotClass != 'per-vertex':
            continue

        if (elem.InputSlot, elem.AlignedByteOffset) in seen_offsets:
            continue
        seen_offsets.add((elem.InputSlot, elem.AlignedByteOffset))

        if elem.name == 'POSITION':
            if 'POSITION.w' in mesh.vertex_layers_float:
                vertex[elem.name] = pos + [mesh.vertex_layers_float['POSITION.w'].data[blender_loop_vertex.vertex_index].value]
            else:
                vertex[elem.name] = elem.pad(pos, 1.0)
        elif elem.name.startswith('COLOR'):
            if elem.name in mesh.vertex_colors:
                vertex[elem.name] = elem.clip(list(mesh.vertex_colors[elem.name].data[blender_loop_vertex.index].color))
            else:
                try:
                    vertex[elem.name] = list(mesh.vertex_colors[elem.name+'.RGB'].data[blender_loop_vertex.index].color)[:3] + \
                                            [mesh.vertex_colors[elem.name+'.A'].data[blender_loop_vertex.index].color[0]]
                except KeyError:
                    raise Fatal("ERROR: Unable to find COLOR property. Ensure the model you are exporting has a color attribute (of type Face Corner/Byte Color) called COLOR")
        elif elem.name == 'NORMAL':
            vertex[elem.name] = elem.pad(blp_normal, 0.0)
        elif elem.name.startswith('TANGENT'):
            vertex[elem.name] = elem.pad(export_Outline.get(blender_loop_vertex.vertex_index, blp_normal), blender_loop_vertex.bitangent_sign)
        elif elem.name.startswith('BINORMAL'):
            pass
        elif elem.name.startswith('BLENDINDICES'):
            i = elem.SemanticIndex * 4
            vertex[elem.name] = elem.pad([ x.group for x in vertex_groups[i:i+4] ], 0)
        elif elem.name.startswith('BLENDWEIGHT'):
            # TODO: Warn if vertex is in too many vertex groups for this layout
            i = elem.SemanticIndex * 4
            vertex[elem.name] = elem.pad([ x.weight for x in vertex_groups[i:i+4] ], 0.0)
        elif elem.name.startswith('TEXCOORD') and elem.is_float():
            # FIXME: Handle texcoords of other dimensions
            uvs = []
            for uv_name in ('%s.xy' % elem.name, '%s.zw' % elem.name):
                if uv_name in texcoords:
                    uvs += list(texcoords[uv_name][blender_loop_vertex.index])

            vertex[elem.name] = uvs
        else:
            # Unhandled semantics are saved in vertex layers
            data = []
            for component in 'xyzw':
                layer_name = '%s.%s' % (elem.name, component)
                if layer_name in mesh.vertex_layers_int:
                    data.append(mesh.vertex_layers_int[layer_name].data[blender_loop_vertex.vertex_index].value)
                elif layer_name in mesh.vertex_layers_float:
                    data.append(mesh.vertex_layers_float[layer_name].data[blender_loop_vertex.vertex_index].value)
            if data:
                vertex[elem.name] = data

        if elem.name not in vertex:
            print('NOTICE: Unhandled vertex element: %s' % elem.name)

    return vertex

def write_fmt_file(f, vb, ib):
    f.write('stride: %i\n' % vb.layout.stride)
    f.write('topology: %s\n' % vb.topology)
    if ib is not None:
        f.write('format: %s\n' % ib.format)
    f.write(vb.layout.to_string())

def collect_vb(folder, name, classification, stride): 
    position = bytearray()
    blend = bytearray()
    texcoord = bytearray()
    with open(os.path.join(folder, f"{name}{classification}.vb"), "rb") as f:
        data = f.read()
        data = bytearray(data)
        i = 0
        while i < len(data):
            import binascii
            position += data[i:i+40]
            blend += data[i+40:i+72]
            texcoord += data[i+72:i+stride]
            i += stride
    return position, blend, texcoord


def collect_ib(folder, name, classification, offset):
    ib = bytearray()
    with open(os.path.join(folder, f"{name}{classification}.ib"), "rb") as f:
        data = f.read()
        data = bytearray(data)
        i = 0
        while i < len(data):
            ib += struct.pack('1I', struct.unpack('1I', data[i:i+4])[0]+offset)
            i += 4
    return ib


def collect_vb_single(folder, name, classification, stride): 
    result = bytearray()
    with open(os.path.join(folder, f"{name}{classification}.vb"), "rb") as f:
        data = f.read()
        data = bytearray(data)
        i = 0
        while i < len(data):
            result += data[i:i+stride]
            i += stride
    return result


# Parsing the headers for vb0 txt files
# This has been constructed by the collect script, so its headers are much more accurate than the originals
def parse_buffer_headers(headers, filters):
    results = []
    # https://docs.microsoft.com/en-us/windows/win32/api/dxgiformat/ne-dxgiformat-dxgi_format
    for element in headers.split("]:")[1:]:
        lines = element.strip().splitlines()
        name = lines[0].split(": ")[1]
        index = lines[1].split(": ")[1]
        data_format = lines[2].split(": ")[1]
        bytewidth = sum([int(x) for x in re.findall("([0-9]*)[^0-9]", data_format.split("_")[0]+"_") if x])//8

        # A bit annoying, but names can be very similar so need to match filter format exactly
        element_name = name
        if index != "0":
            element_name += index
        if element_name+":" not in filters:
            continue

        results.append({"semantic_name": name, "element_name": element_name, "index": index, "format": data_format, "bytewidth": bytewidth})

    return results


@orientation_helper(axis_forward='-Z', axis_up='Y')
class Import3DMigotoFrameAnalysis(bpy.types.Operator, ImportHelper, IOOBJOrientationHelper):
    """Import a mesh dumped with 3DMigoto's frame analysis"""
    bl_idname = "import_mesh.migoto_frame_analysis"
    bl_label = "Import 3DMigoto Frame Analysis Dump"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = '.txt'
    filter_glob : StringProperty(
            default='*.txt',
            options={'HIDDEN'},
            )

    files : CollectionProperty(
            name="File Path",
            type=bpy.types.OperatorFileListElement,
            )

    flip_texcoord_v : BoolProperty(
            name="Flip TEXCOORD V",
            description="Flip TEXCOORD V asix during importing",
            default=True,
            )

    load_related : BoolProperty(
            name="Auto-load related meshes",
            description="Automatically load related meshes found in the frame analysis dump",
            default=True,
            )

    load_buf : BoolProperty(
            name="Load .buf files instead",
            description="Load the mesh from the binary .buf dumps instead of the .txt files\nThis will load the entire mesh as a single object instead of separate objects from each draw call",
            default=False,
            )

    merge_meshes : BoolProperty(
            name="Merge meshes together",
            description="Merge all selected meshes together into one object. Meshes must be related",
            default=False,
            )

    pose_cb : StringProperty(
            name="Bone CB",
            description='Indicate a constant buffer slot (e.g. "vs-cb2") containing the bone matrices',
            default="",
            )

    pose_cb_off : bpy.props.IntVectorProperty(
            name="Bone CB range",
            description='Indicate start and end offsets (in multiples of 4 component values) to find the matrices in the Bone CB',
            default=[0,0],
            size=2,
            min=0,
            )

    pose_cb_step : bpy.props.IntProperty(
            name="Vertex group step",
            description='If used vertex groups are 0,1,2,3,etc specify 1. If they are 0,3,6,9,12,etc specify 3',
            default=1,
            min=1,
            )

    def get_vb_ib_paths(self):
        buffer_pattern = re.compile(r'''-(?:ib|vb[0-9]+)(?P<hash>=[0-9a-f]+)?(?=[^0-9a-f=])''')

        dirname = os.path.dirname(self.filepath)
        ret = set()

        files = []
        if self.load_related:
            for filename in self.files:
                match = buffer_pattern.search(filename.name)
                if match is None or not match.group('hash'):
                    continue
                paths = glob(os.path.join(dirname, '*%s*.txt' % filename.name[match.start():match.end()]))
                files.extend([os.path.basename(x) for x in paths])
        if not files:
            files = [x.name for x in self.files]

        for filename in files:
            match = buffer_pattern.search(filename)
            if match is None:
                raise Fatal('Unable to find corresponding buffers from filename - ensure you are loading a dump from a timestamped Frame Analysis directory (not a deduped directory)')

            use_bin = self.load_buf
            if not match.group('hash') and not use_bin:
                self.report({'INFO'}, 'Filename did not contain hash - if Frame Analysis dumped a custom resource the .txt file may be incomplete, Using .buf files instead')
                use_bin = True # FIXME: Ask

            ib_pattern = filename[:match.start()] + '-ib*' + filename[match.end():]
            vb_pattern = filename[:match.start()] + '-vb*' + filename[match.end():]
            ib_paths = glob(os.path.join(dirname, ib_pattern))
            vb_paths = glob(os.path.join(dirname, vb_pattern))

            if vb_paths and use_bin:
                vb_bin_paths = [ os.path.splitext(x)[0] + '.buf' for x in vb_paths ]
                ib_bin_paths = [ os.path.splitext(x)[0] + '.buf' for x in ib_paths ]
                if all([ os.path.exists(x) for x in itertools.chain(vb_bin_paths, ib_bin_paths) ]):
                    # When loading the binary files, we still need to process
                    # the .txt files as well, as they indicate the format:
                    ib_paths = list(zip(ib_bin_paths, ib_paths))
                    vb_paths = list(zip(vb_bin_paths, vb_paths))
                else:
                    self.report({'WARNING'}, 'Corresponding .buf files not found - using .txt files')
                    use_bin = False

            pose_path = None
            if self.pose_cb:
                pose_pattern = filename[:match.start()] + '*-' + self.pose_cb + '=*.txt'
                try:
                    pose_path = glob(os.path.join(dirname, pose_pattern))[0]
                except IndexError:
                    pass

            if len(ib_paths) != 1 or len(vb_paths) != 1:
                raise Fatal('Only draw calls using a single vertex buffer and a single index buffer are supported for now')
            ret.add((vb_paths[0], ib_paths[0], use_bin, pose_path))
        return ret

    def execute(self, context):
        if self.load_buf:
            # Is there a way to have the mutual exclusivity reflected in
            # the UI? Grey out options or use radio buttons or whatever?
            if self.merge_meshes or self.load_related:
                self.report({'INFO'}, 'Loading .buf files selected: Disabled incompatible options')
            self.merge_meshes = False
            self.load_related = False

        try:
            keywords = self.as_keywords(ignore=('filepath', 'files', 'filter_glob', 'load_related', 'load_buf', 'pose_cb'))
            paths = self.get_vb_ib_paths()

            import_3dmigoto(self, context, paths, **keywords)
        except Fatal as e:
            self.report({'ERROR'}, str(e))
        return {'FINISHED'}
    
def get_override(area_type, region_type):
    for area in bpy.context.window.screen.areas:
        if area.type == area_type:
            for region in area.regions:
                if region.type == region_type:
                    return {'area': area, 'region': region}
    return None

def apply_transform(obj):
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

class MY_ADDON_PT_main_panel(bpy.types.Panel):
    bl_label = "GIMI SCRIPTS"
    bl_idname = "PT_MainPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Gimi Scripts'

    def draw(self, context):
        layout = self.layout

        # Transfer Properties
        box = layout.box()
        box.label(text="Transfer Properties", icon='ARROW_LEFTRIGHT')
        row = box.row()
        row.prop_search(context.scene, "base_object", bpy.data, "objects", text="Base Object")
        row = box.row()
        row.prop_search(context.scene, "target_object", bpy.data, "objects", text="Target Object")
        row = box.row()
        row.operator("my_addon.transfer_properties", text="Transfer Custom Properties", icon='MESH_ICOSPHERE')
        # Fill VG's and Remove Unused Vertex Groups
        box = layout.box()
        box.label(text="Vertex Groups", icon='GROUP_VERTEX')
        row = box.row()
        row.prop(context.scene, "Largest_VG", text="Largest VG")
        row = box.row()
        row.operator("my_addon.fill_vgs", text="Fill Vertex Groups", icon='ADD')
        row = box.row()
        row.operator("my_addon.remove_unused_vgs", text="Remove Unused VG's", icon='X')
        row = box.row()
        row.operator("my_addon.remove_all_vgs", text="Remove All VG's", icon='CANCEL')
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
        box.label(text="Vertex Group REMAP", icon='ARROW_LEFTRIGHT')
        row = box.row()
        row.prop_search(context.scene, "vgm_source_object", bpy.data, "objects", text="Source")
        row = box.row()
        row.prop_search(context.scene, "vgm_destination_object", bpy.data, "objects", text="Target")
        row = box.row()
        row.operator("object.vertex_group_remap", text="Run Remap")     
        # Bones
        box = layout.box()
        box.label(text="Bones", icon='BONE_DATA')
        row = box.row()
        row.prop_search(context.scene, "bone_object", bpy.data, "objects", text="Bone Object")
        row = box.row()
        row.operator("my_addon.bone_deletion", text="Bone Deletion", icon='X')
        # Data Utility
        box = layout.box()
        box.label(text="Data Utility", icon='SETTINGS')
        row = box.row()
        row.operator("my_addon.color_attribute", text="Color Attribute", icon='COLOR')
        row = box.row()
        row.operator("my_addon.uv_map", text="UV Map",icon='UV_FACESEL')
        
class OBJECT_OT_merge_vertex_groups(bpy.types.Operator):
    bl_idname = "object.merge_vertex_groups"
    bl_label = "Merge Vertex Groups"

    def execute(self, context):
        # Retrieve user choices
        mode = context.scene.merge_mode
        vertex_groups = context.scene.vertex_groups
        smallest_group_number = context.scene.smallest_group_number
        largest_group_number = context.scene.largest_group_number

        # Your existing code for merging vertex groups goes here
        # Use mode, vertex_groups, smallest_group_number, largest_group_number to access user choices

        selected_obj = [obj for obj in bpy.context.selected_objects]
        vgroup_names = []

        if mode == 'MODE1':
            vgroup_names = [vertex_groups]
        elif mode == 'MODE2':
            vgroup_names = [[f"{i}" for i in range(smallest_group_number, largest_group_number + 1)]]
        elif mode == 'MODE3':
            vgroup_names = [[x.name.split(".")[0] for x in y.vertex_groups] for y in selected_obj]
        else:
            self.report({'ERROR'}, "Mode not recognized, exiting")
            return {'CANCELLED'}

        if not vgroup_names:
            self.report({'ERROR'}, "No vertex groups found, please double check an object is selected and required data has been entered")
            return {'CANCELLED'}

        for cur_obj, cur_vgroup in zip(selected_obj, itertools.cycle(vgroup_names)):
            for vname in cur_vgroup:
                relevant = [x.name for x in cur_obj.vertex_groups if x.name.split(".")[0] == f"{vname}"]

                if relevant:
                    vgroup = cur_obj.vertex_groups.new(name=f"x{vname}")

                    for vert_id, vert in enumerate(cur_obj.data.vertices):
                        available_groups = [v_group_elem.group for v_group_elem in vert.groups]

                        combined = 0
                        for v in relevant:
                            if cur_obj.vertex_groups[v].index in available_groups:
                                combined += cur_obj.vertex_groups[v].weight(vert_id)

                        if combined > 0:
                            vgroup.add([vert_id], combined, 'ADD')

                    for vg in [x for x in cur_obj.vertex_groups if x.name.split(".")[0] == f"{vname}"]:
                        cur_obj.vertex_groups.remove(vg)

                    for vg in cur_obj.vertex_groups:
                        if vg.name[0].lower() == "x":
                            vg.name = vg.name[1:]

            bpy.context.view_layer.objects.active = cur_obj
            bpy.ops.object.vertex_group_sort()

        return {'FINISHED'}   

class MY_ADDON_OT_color_attribute(bpy.types.Operator):
    bl_label = "Color Attribute"
    bl_idname = "my_addon.color_attribute"

    def execute(self, context):
        scene = bpy.context.scene
        bpy.context.scene.cursor.location = (0, 0, 0)
        selected = bpy.context.selected_objects
        bpy.context.scene.tool_settings.transform_pivot_point = 'CURSOR' 

        for obj in selected:
            bpy.ops.object.mode_set(mode='EDIT')
            bm = bmesh.from_edit_mesh(obj.data)
            names = [a.name for a in obj.data.attributes]
            if 'COLOR' not in names:
                collayer = bm.loops.layers.color.new('COLOR')
                for v in bm.verts:
                    for l in v.link_loops:
                        l[collayer] = [1, 0.502, 0.502, 0.5]
            bpy.ops.object.mode_set(mode='OBJECT')

        return {'FINISHED'}

class MY_ADDON_OT_uv_map(bpy.types.Operator):
    bl_label = "Create UV Map"
    bl_idname = "my_addon.uv_map"

    def execute(self, context):
        bpy.context.scene.cursor.location = (0, 0, 0)
        selected = bpy.context.selected_objects
        bpy.context.scene.tool_settings.transform_pivot_point = 'CURSOR'
        scene = bpy.context.scene

        for obj in selected:
            bpy.ops.object.mode_set(mode = 'OBJECT')
            # check if it has uvmap called texcoord.xy
            # if not, rename first uvmap to texcoord.xy
            uvs = obj.data.uv_layers
            if len(uvs) == 0:
                uvs.new(name='TEXCOORD.xy')
            if 'TEXCOORD.xy' not in uvs:
                uvs[0].name = 'TEXCOORD.xy'

            # check if it has uvmap called texcoord1.xy
            # if not, duplicate texcoord.xy to texcoord1.xy
            if 'TEXCOORD1.xy' not in uvs:
                newuv = uvs.new(name='TEXCOORD1.xy')
                for loop in obj.data.loops:
                    newuv.data[loop.index].uv = uvs['TEXCOORD.xy'].data[loop.index].uv
        return {'FINISHED'}

class MY_ADDON_OT_bone_deletion(bpy.types.Operator):
    bl_label = "Bone Deletion"
    bl_idname = "my_addon.bone_deletion"

    def execute(self, context):
        bone_object = context.scene.bone_object

        if bone_object:
            selected_bones = [bone for bone in bone_object.data.edit_bones if bone.select]
            for selected_bone in selected_bones:
                target = self.find_parent_not_in_collection(selected_bone, selected_bones)
                self.remove_bone(selected_bone, target)

        return {'FINISHED'}

    def transfer_weights(self, source, target, obj):
        source_group = obj.vertex_groups.get(source.name)
        if source_group is None:
            return
        source_i = source_group.index
        target_group = obj.vertex_groups.get(target.name)
        if target_group is None:
            target_group = obj.vertex_groups.new(name=target.name)

        for v in obj.data.vertices:
            for g in v.groups:
                if g.group == source_i:
                    target_group.add((v.index,), g.weight, 'ADD')
        obj.vertex_groups.remove(source_group)

    def remove_bone(self, source, target):
        for o in bpy.data.objects:
            self.transfer_weights(source, target, o)
        edit_bone = bpy.context.object.data.edit_bones.get(source.name)
        bpy.context.object.data.edit_bones.remove(edit_bone)

    def find_parent_not_in_collection(self, bone, collection):
        if bone.parent in collection:
            return self.find_parent_not_in_collection(bone.parent, collection)
        else:
            return bone.parent

class MY_ADDON_OT_remove_all_vgs(bpy.types.Operator):
    bl_label = "Remove All VG's"
    bl_idname = "my_addon.remove_all_vgs"
   

    def execute(self, context):
        selected_object = bpy.context.active_object

        if selected_object and selected_object.type == 'MESH':
            # Removendo todos os VGs
            for group in selected_object.vertex_groups:
                selected_object.vertex_groups.remove(group)

        return {'FINISHED'}

class MY_ADDON_OT_transfer_properties(bpy.types.Operator):
    bl_label = "Transfer Custom Properties"
    bl_idname = "my_addon.transfer_properties"
    bl_description = "Transfer custom 3DMigoto properties to another object"


    def execute(self, context):
        base_object = context.scene.base_object
        target_object = context.scene.target_object

        if base_object and target_object:
            # Transfer object custom properties
            for k in base_object.keys():
                target_object[k] = base_object[k]

        return {'FINISHED'}

class MY_ADDON_OT_fill_vgs(bpy.types.Operator):
    bl_label = "Fill Vertex Groups"
    bl_idname = "my_addon.fill_vgs"
    bl_description = "Fill the VG's based on Largest input and sort the VG's"

    def execute(self, context):
        selected_object = bpy.context.active_object
        largest = context.scene.Largest_VG  # Use o valor de Largest_VG aqui
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

class MY_ADDON_OT_remove_unused_vgs(bpy.types.Operator):
    bl_label = "Remove Unused VG's"
    bl_idname = "my_addon.remove_unused_vgs"
    bl_description = "Remove all Empty VG's"

    def execute(self, context):
        # Verifica se há um objeto ativo
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
            # Se nenhum objeto estiver selecionado, emite uma mensagem de erro
            self.report({'ERROR'}, "No objects selected")
            return {'CANCELLED'}
        
class OBJECT_OT_vertex_group_remap(bpy.types.Operator):
    bl_idname = "object.vertex_group_remap"
    bl_label = "Vertex Group Remap"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Your original code here
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

        # Rest of your code
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

        # Finally, fill in missing spots and sort vertex groups
        missing = set([f"{i}" for i in range(original_vg_length)]) - set([x.name.split(".")[0] for x in destination_object.vertex_groups])
        for number in missing:
            destination_object.vertex_groups.new(name=f"{number}")

        # I'm not sure if it is possible to sort/add vertex groups without setting the current object and using ops
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
                # Goes into the left branch, then the right branch if needed
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
        default=True,
        description="Enable Tri to Quads"
    )
    merge_by_distance: BoolProperty(
        name="Merge by Distance",
        default=True,
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
    bl_label = "Quick Import Toolbox"
    bl_idname = "PT_QuickImportPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Gimi Scripts'
 
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
    bl_description = "Setup Character for GIMI/SRMI"

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

        # Optionally go to edit mode and perform additional actions
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

        return {"FINISHED"}
        
def menu_func_import(self, context):
    self.layout.operator(QuickImport.bl_idname, text="Quick Import for GIMI")    
    
def register():
    bpy.utils.register_class(MY_ADDON_PT_main_panel)
    bpy.utils.register_class(MY_ADDON_OT_bone_deletion)
    bpy.utils.register_class(MY_ADDON_OT_transfer_properties)
    bpy.utils.register_class(MY_ADDON_OT_fill_vgs)
    bpy.utils.register_class(MY_ADDON_OT_remove_unused_vgs)
    bpy.utils.register_class(MY_ADDON_OT_remove_all_vgs)
    bpy.utils.register_class(MY_ADDON_OT_color_attribute)
    bpy.utils.register_class(MY_ADDON_OT_uv_map)
    bpy.types.Scene.base_object = bpy.props.PointerProperty(type=bpy.types.Object)
    bpy.types.Scene.target_object = bpy.props.PointerProperty(type=bpy.types.Object)
    bpy.types.Scene.Largest_VG = bpy.props.IntProperty()
    bpy.types.Scene.bone_object = bpy.props.PointerProperty(type=bpy.types.Object)
    bpy.utils.register_class(OBJECT_OT_vertex_group_remap)
    bpy.types.Scene.vgm_source_object = bpy.props.PointerProperty(type=bpy.types.Object)
    bpy.types.Scene.vgm_destination_object = bpy.props.PointerProperty(type=bpy.types.Object)
    #bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    register_class(QuickImport)
    register_class(QuickImportPanel)
    register_class(Import3DMigotoFrameAnalysis)
    bpy.utils.register_class(OBJECT_OT_merge_vertex_groups)
    bpy.types.Scene.merge_mode = bpy.props.EnumProperty(items=[
        ('MODE1', 'Mode 1: Single VG', 'Merge based on specific vertex groups'),
        ('MODE2', 'Mode 2: By Range ', 'Merge based on a range of vertex groups'),
        ('MODE3', 'Mode 3: All VG', 'Merge all vertex groups')],
        default='MODE3')
    bpy.types.Scene.vertex_groups = bpy.props.StringProperty(name="Vertex Groups", default="")
    bpy.types.Scene.smallest_group_number = bpy.props.IntProperty(name="Smallest Group", default=0)
    bpy.types.Scene.largest_group_number = bpy.props.IntProperty(name="Largest Group", default=999)
    bpy.utils.register_class(QuickImportSettings)
    bpy.types.Scene.quick_import_settings = PointerProperty(type=QuickImportSettings)


def unregister():
    bpy.utils.unregister_class(MY_ADDON_PT_main_panel)
    bpy.utils.unregister_class(MY_ADDON_OT_bone_deletion)
    bpy.utils.unregister_class(MY_ADDON_OT_transfer_properties)
    bpy.utils.unregister_class(MY_ADDON_OT_fill_vgs)
    bpy.utils.unregister_class(MY_ADDON_OT_remove_unused_vgs)
    bpy.utils.unregister_class(MY_ADDON_OT_remove_all_vgs)
    bpy.utils.unregister_class(MY_ADDON_OT_color_attribute)
    bpy.utils.unregister_class(MY_ADDON_OT_uv_map)
    del bpy.types.Scene.base_object
    del bpy.types.Scene.target_object
    del bpy.types.Scene.Largest_VG
    del bpy.types.Scene.bone_object
    #bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    unregister_class(QuickImport)
    unregister_class(QuickImportPanel)
    unregister_class(Import3DMigotoFrameAnalysis)
    bpy.utils.unregister_class(OBJECT_OT_merge_vertex_groups)
    del bpy.types.Scene.merge_mode
    del bpy.types.Scene.vertex_groups
    del bpy.types.Scene.smallest_group_number
    del bpy.types.Scene.largest_group_number
    bpy.utils.unregister_class(QuickImportSettings)
    del bpy.types.Scene.quick_import_settings
    bpy.utils.unregister_class(OBJECT_OT_vertex_group_remap)
    del bpy.types.Scene.vgm_source_object
    del bpy.types.Scene.vgm_destination_object


if __name__ == "__main__":
    register()
    
