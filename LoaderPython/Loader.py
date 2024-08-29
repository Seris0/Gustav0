import os
import ctypes
import sys
import psutil
from pyinjector import inject
import subprocess

def check_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def parse_ini_settings(config_path, setting_key):
    if not os.path.exists(config_path):
        print(f"Error: Configuration file {config_path} not found.")
        return []

    settings = []
    with open(config_path, 'r') as file:
        for line in file:
            if line.strip().startswith(setting_key):
                value = line.strip().split('=', 1)[1].strip()
                if os.path.exists(value):
                    settings.append(value)
                else:
                    base_dir = os.path.dirname(config_path)
                    full_path = os.path.join(base_dir, value)
                    if os.path.exists(full_path):
                        settings.append(full_path)
                    else:
                        settings.append(value)
    return settings

def main():
    print("------------------------------- 3DMigoto SRMI Loader ------------------------------\n")
    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    print(f"Working directory: {base_dir}")
    
    migoto_lib_path = os.path.join(base_dir, "d3d11.dll")
    config_path = os.path.join(base_dir, "d3dx.ini")
    
    startup_commands = parse_ini_settings(config_path, "launch")
    for cmd in startup_commands:
        print(f"Executing startup command: {cmd}")
        try:
            subprocess.Popen(cmd)
        except Exception as e:
            print(f"Command execution failed: {e}")
            continue  

    if not os.path.exists(migoto_lib_path):
        print(f"Error: 3DMigoto library {migoto_lib_path} not found.")
    else:
        print(f"Located: {migoto_lib_path}")

    additional_libs = parse_ini_settings(config_path, "proxy")
    for lib_path in additional_libs:
        lib_path = os.path.abspath(lib_path)
        if not os.path.exists(lib_path):
            print(f"Error: Additional library {lib_path} not found.")
        else:
            print(f"Located: {lib_path}")

    target_apps = parse_ini_settings(config_path, "target")
    if not target_apps:
        print("Error: No target application specified in the configuration.")
    else:
        for app in target_apps:
            print(f"Target application: {app}\n")

    print("Note: This window may close automatically when the application starts.\n")
    print("3DMigoto Ready - Please launch the application now.")
    
    while True:
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                for app in target_apps:
                    if proc.info['name'] == os.path.basename(app) or proc.info['name'] == app:
                        print(f"Application detected: {proc.info['name']} (PID: {proc.info['pid']})")
                        try:
                            inject(proc.info['pid'], migoto_lib_path)
                            print("3DMigoto library injection successful.")
                            
                            for lib_path in additional_libs:
                                if os.path.exists(lib_path):
                                    try:
                                        inject(proc.info['pid'], lib_path)
                                        print(f"Additional library injection successful: {lib_path}")
                                    except Exception as e:
                                        print(f"Failed to inject additional library {lib_path}: {e}")
                            
                            return
                        except Exception as e:
                            print(f"Library injection failed: {e}")
                            print("Retrying injection shortly...")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

if __name__ == "__main__":
    if not check_admin():
        print("Please run this program with administrative privileges.")
        input()
        sys.exit()
    
    main()
