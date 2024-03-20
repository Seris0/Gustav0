import re
import os
import shutil
import argparse

def remove_lines(file_path, patterns):
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    changes_made = False
    for pattern in patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, '', content)
            changes_made = True

    if changes_made:
        backup_path = os.path.join(os.path.dirname(file_path), f'backup_{file_name}.txt')
        shutil.copyfile(file_path, backup_path)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f'Linhas removidas de {file_path}')
    else:
        print(f'No necessary changes in {file_path}')

def process_ini_files(directory_path, patterns, recursive=False):
    for root, dirs, files in os.walk(directory_path):
        for filename in files:
            if filename.lower() != 'desktop.ini' and filename.endswith('.ini'):
                file_path = os.path.join(root, filename)
                remove_lines(file_path, patterns)

        if not recursive:
            break

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

def process_ini_files_with_orfix(directory, recursive=False):
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
            modified_files.append(ini_file)
        else:
            print("No changes necessary in the file.")

    return modified_files

def main():
    parser = argparse.ArgumentParser(description='Remove specific lines and add ORFix to .ini files')
    parser.add_argument('-r', '--recursive', action='store_true', help='Process recursively in subdirectories')
    args = parser.parse_args()

    pattern_1 = re.compile(r'\$CharacterIB = \d+\n(?:ResourceRef\w+ = reference ps-t\d+\n)+')
    pattern_2 = re.compile(r'; Generated shader fix for 3.0\+ GIMI importer characters.*?;endif', re.DOTALL)

    directory_path = os.getcwd()

    process_ini_files(directory_path, [pattern_1, pattern_2], recursive=args.recursive)
    process_ini_files_with_orfix(directory_path, recursive=args.recursive)

if __name__ == '__main__':
    main()
