import os

def find_vb0_file(directory):
    return next((f for f in os.listdir(directory) if "vb0" in f and f.endswith(".txt")), None)

def read_write_file(file_path, mode, content=None):
    with open(file_path, mode) as file:
        return file.readlines() if mode == 'r' else file.writelines(content)

def process_lines(lines):
    processed_lines = []
    skip_element = False
    
    for i, line in enumerate(lines):
        if line.strip().startswith('element['):
            if 'SemanticName: COLOR' in lines[i+1] or 'SemanticName: TEXCOORD' in lines[i+1]:
                skip_element = True
            else:
                skip_element = False
                processed_lines.append(line)
        elif skip_element and line.strip().startswith('InstanceDataStepRate:'):
            skip_element = False
        elif not skip_element:
            processed_lines.append('stride: 40\n' if line.strip().startswith('stride:') else line)
    
    return [line for line in processed_lines if 'TEXCOORD' not in line and 'COLOR' not in line]

def process_vb0_file():
    cwd = os.getcwd()
    vb0_file = find_vb0_file(cwd)
    
    if vb0_file:
        file_path = os.path.join(cwd, vb0_file)
        lines = read_write_file(file_path, 'r')
        processed_lines = process_lines(lines)
        read_write_file(file_path, 'w', processed_lines)
        print(f"Processed file: {vb0_file}")
    else:
        print("No file with 'vb0' in the name found in the current working directory.")

if __name__ == "__main__":
    process_vb0_file()
    input("Press Enter to exit...")