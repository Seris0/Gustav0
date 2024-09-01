import os

def merge_ib_files(output_file, *input_files):
    with open(output_file, 'wb') as outfile:
        for input_file in input_files:
            with open(input_file, 'rb') as infile:
                outfile.write(infile.read())

current_directory = os.getcwd()
file_endings = ['Body.ib', 'Head.ib', 'Dress.ib']

input_files = [os.path.join(current_directory, file) for file in os.listdir(current_directory) if file.endswith(tuple(file_endings))]
input_files.sort(key=lambda x: file_endings.index(next(ending for ending in file_endings if x.endswith(ending))))

output_file = 'Combined.ib'
output_path = os.path.join(current_directory, output_file)

if input_files:
    merge_ib_files(output_path, *input_files)
    print(f"Files merged successfully. Output: {output_path}")
    print("Merged files:")
    for file in input_files:
        print(f"- {file}")
else:
    print("No matching files found.")