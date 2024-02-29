#Gustav0
#Remove Old Reflection from all ini files
#1.0

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
        backup_path = f'backup_{file_name}.txt'  
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

def main():
    parser = argparse.ArgumentParser(description='Remove linhas específicas dos arquivos')
    parser.add_argument('-r', '--recursive', action='store_true', help='Processar recursivamente em subdiretórios')
    args = parser.parse_args()
    pattern_1 = re.compile(r'\$CharacterIB\s*=\s*\d+\s*[\r\n]+\s*ResourceRefDressDiffuse\s*=\s*reference ps-t0\s*[\r\n]+\s*ResourceRefDressLightMap\s*=\s*reference ps-t2\s*')
    pattern_2 = re.compile(r'; Generated shader fix for 3.0\+ GIMI importer characters.*?;endif', re.DOTALL)

    directory_path = os.getcwd()

    process_ini_files(directory_path, [pattern_1, pattern_2], recursive=args.recursive)

if __name__ == '__main__':
    main()