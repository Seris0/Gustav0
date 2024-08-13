# Made by Gustav0 and SilentNightSound

#Remap Arlecchino mods to Arlecchino First Phase Boss

#Usage instructions:
#1. Make a copy of the Arlecchino mod folder.
#2. Place THIS script inside and execute it.


import os
import struct
import argparse
import shutil


old_vs_new = {
    "6895f405": "cf66bef6", #position
    "e211de60": "5227c79e", #blend
    "8b17a419": "a75e7052", #Texcoord
    "44e3487a": "970e7336", #draw
    "e811d2a1": "480f1267",  #ib
}


remaps = {"6895f405": ('ArlecchinoBoss',[47, 49, 48, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 61, 60, 62,
                                        65, 63, 64, 66, 67, 69, 71, 73, 75, 77, 79, 81, 68, 70, 72, 74, 76, 78, 80, 82, 83, 84, 85, 86, 88, 90, 87, 89, 91,
                                        92, 94, 96, 98, 100, 93, 95, 97, 99, 101, 102, 103, 104, 106, 107, 110, 105, 108, 109, 111, 112, 113, 114, 115, 0, 1, 2,
                                        3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46]),
                       
        }


# Remap Arlecchino First Phase
def remap_arle(folder_path):
    print("\nArlecchino Playable to Boss First Phase REMAP\n\n*******************************************\n")
    print("\n  WARNING, THE ACTION OF THIS SCRIPT IS IRREVERSIBLE, ONLY USE IT INSIDE A SINGLE FOLDER AND MAKE A BACKUP OF YOUR MOD.\n")
    print("\n*******************************************\n")
    
    print("""\nUsage instructions:\n
            1. Make a copy of the Arlecchino mod folder.
            2. Place THIS script inside and execute it.\n""")
    print("Press ENTER if you understand, otherwise please close the window:")
    input()
    
    script_folder_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
    arle_boss_mod_folder = os.path.join(folder_path, f"{script_folder_name} BossVer")
    if not os.path.exists(arle_boss_mod_folder):
        os.makedirs(arle_boss_mod_folder)

    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        if os.path.isfile(file_path):
            if file.lower().endswith(('.ini', '.dds', '.buf', '.ib')):
                shutil.copy(file_path, arle_boss_mod_folder)
            
            if "blend.buf" in file.lower():
                try:
                    shutil.copy(file_path, arle_boss_mod_folder)
                    blend_file_name = os.path.basename(file_path)
                    copied_blend_file_path = os.path.join(arle_boss_mod_folder, blend_file_name)
                    for x, vg_remap in remaps.items():
                        with open(copied_blend_file_path, "rb") as g:
                            blend_data = g.read()
                            remap_data = remap(blend_data, vg_remap[1])
                        with open(copied_blend_file_path, "wb") as g:
                            g.write(remap_data)
                            print(f"File: {blend_file_name} VGs has been remapped successfully for {vg_remap[0]}!")
                    
                except Exception as e:
                    print(f'Error processing file: {file_path}')
                    print(e)
                    continue
                                
            if file.lower().endswith('.ini'):
                try:
                    with open(file_path, 'r', encoding="utf-8") as f:
                        s = f.read()
                        old_stream = s
                    for x, vg_remap in remaps.items():
                        if x not in s:
                            continue
                        same_folder_blends = [blend_file for blend_file in os.listdir(arle_boss_mod_folder)
                                              if os.path.isfile(os.path.join(arle_boss_mod_folder, blend_file)) and
                                              "blend" in blend_file.lower() and ".buf" in blend_file.lower()]
                        if len(same_folder_blends) == 0:
                            continue
                        for blend_file in same_folder_blends:
                            with open(os.path.join(arle_boss_mod_folder, blend_file), "rb") as g:
                                blend_data = g.read()
                                remap_data = remap(blend_data, vg_remap[1])
                            with open(os.path.join(arle_boss_mod_folder, blend_file), "wb") as g:
                                g.write(remap_data)
                                print(f"File: {blend_file} VGs has been remapped successfully!")
                    for old, new in old_vs_new.items():
                        if old in s:
                            s = s.replace(old, new)
                            print (f'   Found {old} ------> Match! hash Remapping to {new}!')
                        elif new in s:
                            print(f'     Found {new} ------> Already Remapped!')
                    if s != old_stream:
                        print(f'File: {file_path} has been modified!')
                    else:
                        print(f'File: {file_path} had no matches. Skipping')
                    
                    new_ini_file = os.path.join(arle_boss_mod_folder, file)
                    with open(new_ini_file, 'w', encoding="utf-8") as f:
                        f.write(s)
                        
                    print(f"New .ini file created: {new_ini_file}")
                    
                except Exception as e:
                    print(f'Error processing file: {file_path}')
                    print(e)
                    continue

def force_remap(folder):
    '''Force remap a character based on the remap options.'''
    print('Remap options:')
    for i, (k,v) in enumerate(remaps.items()):
        print(f'{i+1}: {v[0]}')
    option = -1
    while option == -1:
        try:
            option = int(input('Select a character to remap: ')) - 1
            if option < 0 or option >= len(remaps):
                print('Invalid option')
                option = -1
        except ValueError:
            print('Invalid option')
            option = -1
        for i, (k,v) in enumerate(remaps.items()):
            if option == i:
                option = k
    for file in os.listdir(folder):
        file_path = os.path.join(folder, file)
        if os.path.isfile(file_path) and "blend" in file.lower() and ".buf" in file.lower():
            try:
                with open(file_path, "rb") as g:
                    blend_data = g.read()
                    remap_data = remap(blend_data, remaps)
                with open(file_path, "wb") as g:
                    g.write(remap_data)
                    print(f"File: {file} VGs has been remapped successfully!")
            except Exception as e:
                print(f'Error processing file: {file}')
                print(e)
                continue

def remap(blend_data, vg_remap):
    '''Remap the VG groups in the blend file'''
    stride = 32
    remapped_blend = bytearray()
    if len(blend_data) % stride != 0:
        raise ValueError("Invalid blend file")
        # print("Invalid blend file. Making backup...")
    for i in range(0, len(blend_data), stride):
        # if i+stride > len(blend_data):
        #     continue
        blendweights = struct.unpack_from("<ffff", blend_data, i)
        blendindices = struct.unpack_from("<IIII", blend_data, i + 16)
        outputweights = bytearray()
        outputindices = bytearray()
        outputweights += struct.pack("<ffff", *blendweights)
        for x in range(4):
            if blendweights[x] != 0 and blendindices[x] in vg_remap:
                outputindices += struct.pack("<I", vg_remap[blendindices[x]])
            else:
                outputindices += struct.pack("<I", blendindices[x])
        remapped_blend += outputweights
        remapped_blend += outputindices
    if len(remapped_blend) % stride != 0:
        raise ValueError("Remapped blend file is invalid")
    return remapped_blend

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--force_remap', action='store_true',default=False)
    args = parser.parse_args()

    current_directory = os.path.dirname(os.path.abspath(__file__))

    if args.force_remap:
        force_remap(current_directory)
    else:
        print("Searching for ini files")
        remap_arle(current_directory)
    input('Done!')