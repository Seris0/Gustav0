import os
import json
import argparse

def extract_json_data(folder_names=None, full=False, ib=False, draw=False, pose=False, blend=False, tex=False):
    root_dir = os.getcwd()
    print(f"Diretório atual: {root_dir}")
    
    output_data = {}
    
    allowed_folders = set(folder_names) if folder_names else None
    
    for root, dirs, files in os.walk(root_dir):
        folder_name = os.path.basename(root)
        if allowed_folders is not None and folder_name not in allowed_folders:
            continue
        
        for file_name in files:
            if file_name.endswith('.json'):
                file_path = os.path.join(root, file_name)
                print(f"Analisando arquivo: {file_name} na pasta: {folder_name}")
                
                with open(file_path, 'r') as file:
                    try:
                        json_content = json.load(file)
                    except json.JSONDecodeError:
                        print(f"Erro ao decodificar JSON em {file_path}")
                        continue
                    
                    for item in json_content:
                        component_name = item.get("component_name", "")
                        if component_name.lower() == "face":
                            continue 
                        
                        output_data.setdefault(folder_name, {}).setdefault(component_name, [])
                        for key, value in item.items():
                            if (full or key in ["draw_vb", "position_vb", "blend_vb", "texcoord_vb", "ib"]) and \
                               (ib and key == "ib" or \
                                draw and key == "draw_vb" or \
                                pose and key == "position_vb" or \
                                blend and key == "blend_vb" or \
                                tex and key == "texcoord_vb"):
                                if len(value) > 5:
                                    output_data[folder_name][component_name].append(f"'{value}': #{key}")

    with open("output.txt", "w") as output_file:
        for folder_name, components in output_data.items():
            output_file.write(f"#{folder_name.strip()}:\n")
            for component_name, values in components.items():
                if component_name:
                    output_file.write(f"#{folder_name} {component_name}:\n")
                for value in values:
                    output_file.write(f"{value}\n")
                output_file.write("\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract JSON data.')
    parser.add_argument('-n', '--folders', nargs='+', help='Specify folders to search')
    parser.add_argument('--ib', action='store_true', help='Extract ib data')
    parser.add_argument('--draw', action='store_true', help='Extract draw_vb data')
    parser.add_argument('--pose', action='store_true', help='Extract position_vb data')
    parser.add_argument('--blend', action='store_true', help='Extract blend_vb data')
    parser.add_argument('--tex', action='store_true', help='Extract texcoord_vb data')
    parser.add_argument('--full', action='store_true', help='Extract full data')
    args = parser.parse_args()
    
    
    if not any(vars(args).values()):
       args.full = True
       
    if args.full:
        extract_json_data(folder_names=args.folders, full=True, ib=True, draw=True, pose=True, blend=True, tex=True)
    else:
        extract_json_data(folder_names=args.folders, ib=args.ib, draw=args.draw, pose=args.pose, blend=args.blend, tex=args.tex)
