
#Author: Gustav0
#Description: Generate ORFix on the .ini file inside the script folder.
#Contribution: LeoTorrez for helping to improve logic and prevent accidents
#By default, the script only works inside the mod folder, using the "-r" flag it works in all destination folders, to use it in blender together with the Leotools addon, insert the argument when importing the script.
#V1.1


import os
import argparse

def find_ini_files(directory, recursive=False):
    ini_files = []

    if recursive:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.ini') and file != 'desktop.ini':
                    ini_files.append(os.path.join(root, file))
    else:
        ini_files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and f.endswith('.ini') and f != 'desktop.ini']

    return ini_files

def check_orfix(index, current_section, file_lines, file_path):
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

def process_ini_files(directory, recursive=False):
    modified_files = []

    ini_files = find_ini_files(directory, recursive=recursive)

    for ini_file in ini_files:
        print(f"Processing file: {ini_file}")
        with open(ini_file, 'r') as f:
            lines = f.readlines()

        modified = False
        current_section = None

        for i, line in enumerate(lines):
            line = line.strip()

            if line.startswith('[') and line.endswith(']'):
                current_section = line
            elif current_section and line.startswith('ps-t2'):
                if not check_orfix(i, current_section, lines, ini_file):
                    add_orfix(i, lines, current_section, ini_file)
                    modified = True

        if modified:
            with open(ini_file, 'w') as f:
                f.writelines(lines)
            print("Changes saved in the file.")
            modified_files.append(ini_file)
        else:
            print("No changes necessary in the file.")

    return modified_files

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate ORFix on .ini files in the specified folder.')
    parser.add_argument('-r', '--recursive', action='store_true', help='Enable recursive search for .ini files')
    args = parser.parse_args()

    current_directory = os.getcwd()
    modified_files = process_ini_files(current_directory, recursive=args.recursive)

    if modified_files:
        print("Script executed successfully on the following files:")
        for modified_file in modified_files:
            print(modified_file)
    else:
        print("No .ini files found or no changes made.")
