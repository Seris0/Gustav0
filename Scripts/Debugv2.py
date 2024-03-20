import os
import argparse
import shutil  # Added for moving folders


def rename_folders(directory, prefix, checked_folder_name):
    for folder in os.listdir(directory):
        if os.path.isdir(os.path.join(directory, folder)) and folder != checked_folder_name:
            if not folder.startswith(prefix):
                new_name = f"{prefix}{folder}"
                new_path = os.path.join(directory, new_name)
                os.rename(os.path.join(directory, folder), new_path)
                print(f"Renamed folder: {folder} -> {new_name}")


def undo_rename(directory, prefix):
    disabled_folders = [folder for folder in os.listdir(directory) if
                        os.path.isdir(os.path.join(directory, folder)) and folder.startswith(prefix)
                        and folder != checked_folder_name]

    folders_to_restore = disabled_folders[:len(disabled_folders) // 2]
    folders_to_remain = disabled_folders[len(disabled_folders) // 2:]

    for folder in folders_to_restore:
        new_name = folder.replace(prefix, "", 1)
        new_path = os.path.join(directory, new_name)
        os.rename(os.path.join(directory, folder), new_path)
        print(f"Restored folder: {folder} -> {new_name}")

    print("\nRemaining disabled folders:")
    for folder in folders_to_remain:
        print(f"Remain folder: {folder}")


def enable_folders(directory, prefix):
    disabled_folders = [folder for folder in os.listdir(directory) if
                        os.path.isdir(os.path.join(directory, folder)) and folder.startswith(prefix)
                        and folder != checked_folder_name]

    for folder in disabled_folders:
        new_name = folder.replace(prefix, "", 1)
        new_path = os.path.join(directory, new_name)
        os.rename(os.path.join(directory, folder), new_path)
        print(f"Enabled folder: {folder} -> {new_name}")


def move_disabled_folders(directory, prefix, checked_folder_name):
    checked_folder_path = os.path.join(directory, checked_folder_name)
    os.makedirs(checked_folder_path, exist_ok=True)

    disabled_folders = [folder for folder in os.listdir(directory) if
                        os.path.isdir(os.path.join(directory, folder)) and folder.startswith(prefix)
                        and folder != checked_folder_name]

    for folder in disabled_folders:
        source_path = os.path.join(directory, folder)
        destination_path = os.path.join(checked_folder_path, folder)
        shutil.move(source_path, destination_path)
        print(f"Moved folder to 'Checked': {folder}")


def search_hash_in_ini(directory, hash_string):
    found_files = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".ini"):
                file_path = os.path.join(root, file)

                with open(file_path, 'rb') as f:
                    content = f.read()
                    try:
                        content = content.decode('utf-8')
                    except UnicodeDecodeError:
                        print(f"Error decoding {file_path}. Skipping...")
                        continue

                    if hash_string in content:
                        found_files.append(file_path)

    return found_files


def main():
    parser = argparse.ArgumentParser(description="Folder manipulation script", add_help=False)
    parser.add_argument("--disable", action="store_true", help="Disable folders by adding 'DISABLED ' prefix")
    parser.add_argument("--half", action="store_true", help="Undo 'DISABLED' from half of the folders")
    parser.add_argument("--enable", action="store_true", help="Enable folders by removing 'DISABLED ' prefix")
    parser.add_argument("--inverse", action="store_true", help="Inverse folders by toggling 'DISABLED ' prefix")
    parser.add_argument("--hash", type=str, help="Search for a hash in .ini files and return their paths")
    parser.add_argument("--move", action="store_true", help="Move disabled folders to 'Checked' folder")

    args, unknown = parser.parse_known_args()

    if "--help" in unknown:
        print(parser.format_help())
        return

    directory = os.getcwd()
    prefix = "DISABLED "
    checked_folder_name = "Checked"

    while True:
        if args.disable:
            rename_folders(directory, prefix, checked_folder_name)
            args.disable = False
        elif args.half:
            undo_rename(directory, prefix)
            args.half = False
        elif args.enable:
            enable_folders(directory, prefix)
            args.enable = False
        elif args.inverse:
            inverse_folders(directory, prefix)
            args.inverse = False
        elif args.move:
            move_disabled_folders(directory, prefix, checked_folder_name)
            args.move = False
        elif args.hash:
            hash_files = search_hash_in_ini(directory, args.hash)
            if hash_files:
                print(f"Files with hash '{args.hash}':")
                for file_path in hash_files:
                    print(file_path)
            else:
                print(f"No files found with hash '{args.hash}'")

            args.hash = None
        else:
            user_input = input(
                "\nType '--half', '--enable', '--disable', '--inverse', '--hash <hash_value>', '--move', or press 'Enter' to quit: ")
            if user_input.lower() == 'exit':
                break
            elif user_input.lower() == '--half':
                args.half = True
            elif user_input.lower() == '--enable':
                args.enable = True
            elif user_input.lower() == '--disable':
                args.disable = True
            elif user_input.lower() == '--inverse':
                args.inverse = True
            elif user_input.lower() == '--move':
                args.move = True
            elif user_input.lower() == '--hash':
                args.hash = input("Enter hash value: ")
            elif not user_input:
                break
            elif user_input.lower() == '--help':
                print(parser.format_help())
            else:
                print("Invalid input. Please use one of the specified commands.")


if __name__ == "__main__":
    main()
