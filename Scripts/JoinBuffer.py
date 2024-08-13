import os

def find_buf_files():
    position_file = None
    blend_file = None
    texcoord_file = None
    
    for file in os.listdir(os.getcwd()):
        file_lower = file.lower()
        if file_lower.endswith('position.buf'):
            position_file = file
        elif file_lower.endswith('blend.buf'):
            blend_file = file
        elif file_lower.endswith('texcoord.buf'):
            texcoord_file = file

    if not position_file or not blend_file or not texcoord_file:
        raise FileNotFoundError("No File.")

    return position_file, blend_file, texcoord_file

position_file, blend_file, texcoord_file = find_buf_files()
output_prefix = os.path.splitext(position_file)[0].replace('Position', '')
output_file = f'{output_prefix}.vb'

with open(position_file, 'rb') as pos_file, \
     open(blend_file, 'rb') as blend_file, \
     open(texcoord_file, 'rb') as tex_file:

    pos_data = pos_file.read()
    blend_data = blend_file.read()
    tex_data = tex_file.read()

pos_index = 0
blend_index = 0
tex_index = 0
output_buffer = bytearray()

while pos_index < len(pos_data):
    output_buffer += pos_data[pos_index:pos_index + 40]
    output_buffer += blend_data[blend_index:blend_index + 32]
    output_buffer += tex_data[tex_index:tex_index + 20]
    pos_index += 40
    blend_index += 32
    tex_index += 20

with open(output_file, 'wb') as f_out:
    f_out.write(output_buffer)

print(f"Rebuild: {output_file}")