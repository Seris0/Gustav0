import os
import ctypes
import sys
import psutil
from pyinjector import inject
import subprocess

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def read_ini_commands(ini_path, command_prefix):
    if not os.path.exists(ini_path):
        print(f"Error: INI file path {ini_path} does not exist.")
        return []

    commands = []
    with open(ini_path, 'r') as file:
        for line in file:
            if line.strip().startswith(command_prefix):
                command = line.strip().split('=', 1)[1].strip()
                if os.path.exists(command):
                    commands.append(command)
                else:
                    current_dir = os.path.dirname(ini_path)
                    full_path = os.path.join(current_dir, command)
                    if os.path.exists(full_path):
                        commands.append(full_path)
                    else:
                        commands.append(command)
    return commands

def read_ini_launch_args(ini_path, command_prefix):
    if not os.path.exists(ini_path):
        print(f"Error: INI file path {ini_path} does not exist.")
        return ""

    launch_args = ""
    with open(ini_path, 'r') as file:
        for line in file:
            if line.strip().startswith(command_prefix):
                launch_args = line.strip().split('=', 1)[1].strip()
                break
    return launch_args

def main():
    print("------------------------------- 3DMigoto SRMI Loader ------------------------------\n")
    current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    print(f"Current directory: {current_dir}")
    
    migoto_dll_path = os.path.join(current_dir, "d3d11.dll")
    ini_path = os.path.join(current_dir, "d3dx.ini")
    
    launch_commands = read_ini_commands(ini_path, "launch")
    launch_args = read_ini_launch_args(ini_path, "Launch_args")
    
    for launch_command in launch_commands:
        command_with_args = f"{launch_command} {launch_args}"
        print(f"Launching executable specified in INI file: {command_with_args}")
        try:
            subprocess.Popen(command_with_args)
        except Exception as e:
            print(f"Failed to launch executable: {e}")
            continue  

    if not os.path.exists(migoto_dll_path):
        print(f"Error: 3DMigoto DLL path {migoto_dll_path} does not exist.")
    else:
        print(f"Loaded: {migoto_dll_path}")

    proxy_dll_paths = read_ini_commands(ini_path, "proxy")
    for proxy_dll_path in proxy_dll_paths:
        proxy_dll_path = os.path.abspath(proxy_dll_path)
        if not os.path.exists(proxy_dll_path):
            print(f"Error: Proxy DLL path {proxy_dll_path} does not exist.")
        else:
            print(f"Loaded: {proxy_dll_path}")

    target_executables = read_ini_commands(ini_path, "target")
    if not target_executables:
        print("Error: No target executable specified in the INI file.")
    else:
        for target_exe in target_executables:
            print(f"Target executable found: {target_exe}\n")

    print("Note: This window may close automatically once the game starts.\n")
    print("3DMigoto Read - Please start the game now.")
    
    while True:
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                for target_exe in target_executables:
                    if proc.info['name'] == os.path.basename(target_exe) or proc.info['name'] == target_exe:
                        print(f"Game found: {proc.info['name']} with PID {proc.info['pid']}")
                        try:
                            inject(proc.info['pid'], migoto_dll_path)
                            print("3DMigoto DLL injection successful.")
                            
                            for proxy_dll_path in proxy_dll_paths:
                                if os.path.exists(proxy_dll_path):
                                    try:
                                        inject(proc.info['pid'], proxy_dll_path)
                                        print(f"Proxy DLL injection successful: {proxy_dll_path}")
                                    except Exception as e:
                                        print(f"Failed to inject proxy DLL {proxy_dll_path}: {e}")
                            
                            return
                        except Exception as e:
                            print(f"Failed to inject DLL: {e}")
                            print("Retrying injection in 1 second...")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

if __name__ == "__main__":
    if not is_admin():
        print("Please run this program as an administrator.")
        input()
        sys.exit()
    
    main()
