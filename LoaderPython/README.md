# 3DMigoto SRMI Loader Documentation

This document outlines the main functions of the 3DMigoto SRMI Loader script.

## Functions

### `check_admin()`

Checks if the script is running with administrative privileges.

- **Returns:** `True` if running as admin, `False` otherwise.

### `parse_ini_settings(config_path, setting_key)`

Parses the configuration file for specific settings.

- **Parameters:**
  - `config_path`: Path to the configuration file (d3dx.ini).
  - `setting_key`: The key to search for in the configuration file.
- **Returns:** A list of values associated with the setting key.

### `main()`

The main function that orchestrates the loader's operations.

1. Prints a welcome message and working directory.
2. Locates the 3DMigoto library (d3d11.dll) and configuration file (d3dx.ini).
3. Executes startup commands specified in the configuration.
4. Identifies additional libraries to be injected.
5. Determines target applications from the configuration.
6. Waits for the target application to start.
7. Injects the 3DMigoto library and additional libraries into the target process.

## Usage

1. Ensure the script is run with administrative privileges.
2. Place the script in the same directory as the 3DMigoto files.
3. Configure the `d3dx.ini` file with appropriate settings:
   - `launch`: Startup commands to execute.
   - `proxy`: Additional DLL to inject.
   - `target`: Target application(s) to inject into.
4. Run the script and launch the target application.

## Notes

- The script will automatically close when the injection is successful.
- If injection fails, it will retry shortly.
- Ensure all paths in the configuration file are correct and accessible.