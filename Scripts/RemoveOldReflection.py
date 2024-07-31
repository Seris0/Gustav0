#Gustav0
#Remove Old Reflection from all ini files
#1.1
#Changelog 1.1: New Pattern 1 for more precision


import re
import os
import shutil
import argparse

texts_to_remove = [
    r"""; Generated shader fix for 3.0+ GIMI importer characters. Please contact the tool developers at https://discord.gg/agmg if you have any questions.

; Variables -----------------------

[Constants]
global $CharacterIB
;0=none, 1=head, 2=body, 3=dress, 4=extra, etc.

[Present]
post $CharacterIB = 0

[ResourceRefHeadDiffuse]
[ResourceRefHeadLightMap]
[ResourceRefBodyDiffuse]
[ResourceRefBodyLightMap]
[ResourceRefDressDiffuse]
[ResourceRefDressLightMap]
[ResourceRefExtraDiffuse]
[ResourceRefExtraLightMap]

; ShaderOverride ---------------------------

[ShaderRegexCharReflection]
[ShaderOverrideOutline]
hash=6ce92f3bcc9c03d0
allow_duplicate_hash = True
if $mod_enabled
    run = CommandListOutline
    run = CommandListReflectionTexture
endif
[ShaderRegexCharReflection.pattern]
discard_n\w+ r\d\.\w+\n
lt r\d\.\w+, l\(0\.010000\), r\d\.\w+\n
and r\d\.\w+, r\d\.\w+, r\d\.\w+\n

[ShaderOverrideOutline]
hash=6ce92f3bcc9c03d0
allow_duplicate_hash = True
if $mod_enabled
    run = CommandListOutline
endif
[ShaderOverrideOutline]
hash=6ce92f3bcc9c03d0
allow_duplicate_hash = True
if $mod_enabled
    run = CommandListOutline
endif
[ShaderOverrideOutline]
hash=6ce92f3bcc9c03d0
allow_duplicate_hash = True
if $mod_enabled
    run = CommandListOutline
endif
[ShaderOverrideOutline]
hash=6ce92f3bcc9c03d0
allow_duplicate_hash = True
if $mod_enabled
    run = CommandListOutline
    mov o0\.w, l\(0\)\n
    mov o1\.xyz, r0\.xyzx\n
    mov o1\.w, l\(0.223606795\)
endif"""
]

def remove_lines(file_path, patterns):
    file_name = os.path.splitext(os.path.basename(file_path))[0]  
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        
    changes_made = False
    for text in texts_to_remove:
        content = content.replace(text, "")
        changes_made = True

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

def main():
    parser = argparse.ArgumentParser(description='Remove linhas específicas dos arquivos')
    parser.add_argument('-r', '--recursive', action='store_true', help='Processar recursivamente em subdiretórios')
    args = parser.parse_args()
    pattern_1 = re.compile(r'\$CharacterIB = \d+\n(?:ResourceRef\w+ = reference ps-t\d+\n)+')
    pattern_2 = re.compile(r'; Generated shader fix for 3\.0\+ GIMI importer characters.*?;endif', re.DOTALL)
    pattern_3 = re.compile(r'; Generated shader fix for 3\.0\+ GIMI importer characters.*?endif', re.DOTALL)
    pattern_4 = re.compile(r'drawindexed=auto\n\$CharacterIB = 0\nendif\n\n\[CommandListOutline\]\nif \$CharacterIB != 0\n(.*?)\nendif', re.DOTALL)

    directory_path = os.getcwd()

    process_ini_files(directory_path, [pattern_1, pattern_2, pattern_3, pattern_4], recursive=args.recursive)

if __name__ == '__main__':
    main()