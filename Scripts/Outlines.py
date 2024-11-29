
import os
import argparse


def main():
  
    parser = argparse.ArgumentParser(description="Set outline thickness")
    parser.add_argument("--thickness", type=int, default=0, help="Thickness of outline (0 - no outline, 255 - maximum outline)")
    args = parser.parse_args()

    texcoord_files = [x for x in os.listdir(".") if "Texcoord.buf" in x]
    if len(texcoord_files) == 0:
        print(f"ERROR: unable to find texcoord file. Ensure you are running this in the same folder as CharTexcoord.buf. Exiting")
        return
        
    texcoord_file = ""
    stride = 0
    
    print("Multiple texcoord files found. Please select one:")
    for i, file in enumerate(texcoord_files, 1):
        print(f"{i}. {file}")
    
    while True:
        try:
            selection = int(input("Enter the number of your selection: "))
            if 1 <= selection <= len(texcoord_files):
                texcoord_file = texcoord_files[selection-1]
                ini_file = [x for x in os.listdir(".") if ".ini" in x]
                if len(ini_file) == 0:
                    print(f"ERROR: unable to find .ini file. Ensure you are running this in the same folder as Char.ini. Exiting")
                    return
                if len(ini_file) > 1:
                    print(f"ERROR: more than one .ini file identified {ini_file}. Please remove files until only one remains, then run script again. Exiting")
                    return
                ini_file = ini_file[0]

                with open(ini_file, "r") as f:
                    stride = int(f.read().split(texcoord_file)[0].split("\n")[-2].split("=")[1].strip())
                break
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a valid number.")

    print(f"Texcoord: {texcoord_file}, Stride: {stride}")

    with open(texcoord_file, "rb+") as f:
        print("Removing outlines")
        data = bytearray(f.read())
        i = 0
        while i < len(data):
            data[i+3] = args.thickness
            i += stride

        print("Writing results to new file")
        f.seek(0)
        f.write(data)
        f.truncate()

    print("All operations complete, exiting")


if __name__ == "__main__":
    main()