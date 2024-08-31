import struct
import numpy as np

# Define the stride and format string
stride = 28

# Format string for unpacking the buffer
format_string = '4h 4b 4B 2H 2H 4B'

# Function to convert 16-bit fixed-point to float
def fixed_point_to_float(value, scale=1.0):
    return value * scale / 32768.0  # Scale based on 16-bit fixed-point range

def read_buf_file(filename):
    with open(filename, 'rb') as f:
        while True:
            data = f.read(stride)
            if not data:
                break  # End of file
            
            # Unpack the data using the format string
            unpacked_data = struct.unpack(format_string, data)
            
            # Extract and convert the components
            position = tuple(fixed_point_to_float(x) for x in unpacked_data[0:4])  # Convert position
            normal = unpacked_data[4:8]  # Normal is already in desired format
            color = unpacked_data[8:12]  # Color is already in desired format
            texcoord = tuple(x / 32768.0 for x in unpacked_data[12:14])  # Convert texcoord
            texcoord1 = tuple(x / 32768.0 for x in unpacked_data[14:16])  # Convert texcoord1
            tangent = unpacked_data[16:20]  # Tangent is already in desired format
            
            # Print or process the extracted data
            print(f"Position: {position}")
            print(f"Normal: {normal}")
            print(f"Color: {color}")
            print(f"Texcoord: {texcoord}")
            print(f"Texcoord1: {texcoord1}")
            print(f"Tangent: {tangent}")

# Replace 'your_file.buf' with the path to your .buf file
read_buf_file('AquilaFavoniaPosition.buf')
