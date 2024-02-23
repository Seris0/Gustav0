#Author: Gustav0
#Description: Generate ORFix on the .ini file inside the script folder.
#Contribution: LeoTorrez for helping to improve logic and prevent accidents
#By default, the script only works inside the mod folder, using the "-r" flag it works in all destination folders, to use it in blender together with the Leotools addon, insert the argument when importing the script.
#V1.0

import os
import argparse

def find_ini_file(recursive=False):
    ini_files = []
    
    if recursive:
        for root, dirs, files in os.walk(os.getcwd()):
            for file in files:
                if file.endswith('.ini') and file != 'desktop.ini':
                    ini_files.append(os.path.join(root, file))
    else:
        ini_files = [f for f in os.listdir(os.getcwd()) if os.path.isfile(f) and f.endswith('.ini') and f != 'desktop.ini']

    if not ini_files:
        print("No .ini files found (excluding desktop.ini)")
        return None

    return ini_files[0]

def check_orfix(index, current_section, file_lines, file_path):
    # Check if two lines above ps-t2 contain the word 'NormalMap'
    if index >= 2:
        two_lines_above = file_lines[index - 2]
        ps_t2_line = file_lines[index]

        if 'NormalMap' in two_lines_above and 'ps-t2' in ps_t2_line and 'run = CommandList\\global\\ORFix\\ORFix' not in file_lines[index + 1]:
            print(f"The section '{current_section}' in the file {file_path} does not have the ORFix. Adding the ORFix line.")
            return False
    return True

def add_orfix(index, file_lines, current_section, file_path):
    # Add "run = CommandList\global\ORFix\ORFix" exactly below ps-t2
    file_lines.insert(index + 1, 'run = CommandList\\global\\ORFix\\ORFix\n')
    print(f"ORFix Added in '{current_section}' of the file {file_path}.")

def process_ini_file(ini_file):
    print(f"Processing file: {ini_file}")
    with open(ini_file, 'r') as f:
        lines = f.readlines()

    modified = False
    current_section = None

    for i, line in enumerate(lines):
        line = line.strip()

        # Check if the line is a section
        if line.startswith('[') and line.endswith(']'):
            current_section = line
        elif current_section and line.startswith('ps-t2'):
            # Check if two lines above ps-t2 contain the word 'NormalMap'
            if not check_orfix(i, current_section, lines, ini_file):
                add_orfix(i, lines, current_section, ini_file)
                modified = True

    if modified:
        # Write the changes back to the .ini file
        with open(ini_file, 'w') as f:
            f.writelines(lines)
        print("Changes saved in the file.")
    else:
        print("No changes necessary in the file.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate ORFix on the .ini file inside the script folder.')
    parser.add_argument('-r', '--recursive', action='store_true', help='Enable recursive search for .ini files')
    args = parser.parse_args()

    ini_file = find_ini_file(recursive=args.recursive)

    if ini_file:
        process_ini_file(ini_file)
        print(f"Script executed successfully on the file {ini_file}")
    else:
        print("No .ini file found to process.")