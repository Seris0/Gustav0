import os
import struct
import argparse  

def main():
    parser = argparse.ArgumentParser(description="Set outline thickness")
    parser.add_argument("--thickness", type=int, default=0, help="Thickness of outline (0 - no outline, 255 - maximum outline)")
    args = parser.parse_args()

    buf_file = [x for x in os.listdir(".") if x.endswith(".buf")]
    if len(buf_file) == 0:
        print(f"ERROR: unable to find .buf file. Ensure you are running this in the correct folder. Exiting")
        return
    if len(buf_file) > 1:
        print(f"ERROR: more than one .buf file identified {buf_file}. Please remove files until only one remains, then run the script again. Exiting")
        return
    buf_file = buf_file[0]

    #Gustav0: Well, all solid weapons have stride of 28, so we don't need to read the ini file.
    stride = 28  

    print(f"Reading Buffer File: {buf_file} with stride {stride} bytes")

    with open(buf_file, "rb+") as f:
        data = bytearray(f.read())
        total_rows = len(data) // stride

        for i in range(total_rows):

            # Modify the COLOR row for the thickness (assuming thickness affects the alpha channel)
            data[i * stride + 12 + 3] = args.thickness

        print("Writing results to file")
        f.seek(0)
        f.write(data)
        f.truncate()

    print("Outline thickness has been updated successfully.")

if __name__ == "__main__":
    main()