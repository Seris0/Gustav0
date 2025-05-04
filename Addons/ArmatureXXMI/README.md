# ArmatureXXMI Add-on

## Personal Recommendations

- **Genshin Impact**: MERGED
- **Honkai Star Rail**: MERGED
- **Zenless Zone Zero**: PER-COMPONENT
- **Wuthering Waves**: MERGED initially, but may change based on the skeleton type you import in WWMI

- ## Installation and Usage

1. Copy the `RenameArmatureXXMI.py` script to the Blender add-ons directory.
2. Activate the add-on through the Blender add-ons preferences menu.
3. Use the "ArmatureXXMI" panel in the "XXMI Scripts" section of Blender's 3D editor to access the add-on's functionalities.
4. For a demonstration of the add-on in action, watch the video [here](https://streamable.com/7lf7yw).

This script is an add-on for Blender that facilitates the setup of armatures for certain anime games. It offers various functionalities for vertex group matching, armature mirroring, and character preparation.

For a better experience, use it together with [QuickImportXXMI](https://github.com/Seris0/QuickImportXXMI).

## Important Note

This add-on is intended to be used by advanced users. I will not explain how it works, as an advanced user must understand the terms and actions used.

## Changelog

### Beta Release
- The beta version of the ArmatureXXMI Add-on is now available!

### Massive Speed Improvement
- Optimized the vertex group matching process.
- Reduced processing time significantly by leveraging numpy for batch operations.
- Removed redundant loops and streamlined calculations for better performance.

## Main Features

### 1. Armature Matching Properties
- **armature_mode**: Sets the armature mode (Merged or By Component).
- **mode**: Sets the processing mode (Honkai Star Rail or Zenless Zone Zero).
- **ignore_hair**: Ignores meshes containing "hair" in the name.
- **ignore_head**: Ignores meshes containing "head" in the name.
- **base_collection**: Base collection for weight paint matching.
- **target_collection**: Target collection for weight paint matching.
- **armature**: Armature to rename bones.

### 2. Armature Matching Operator
- **execute**: This method executes the main logic of the script. It processes the base and target collections, matching vertex groups based on weight paint centroids, and renames the armature bones based on the found matches.

### 3. Armature Mirroring Operator
- **execute**: Mirrors the selected armature along the global X-axis.

### 4. Set Armature for Character Operator
- **execute**: Sets up the armature for a character, renaming bones according to a specific pattern.

### 5. Set Character for Armature Operator
- **execute**: Sets up the character for the armature, ensuring that vertex groups have the correct prefix.

### 6. Clean Armature Operator
- **execute**: Cleans the armature by removing bones that are not linked to any vertex groups.

### 7. Split Mesh by Vertex Groups Operator
- **execute**: Split the mesh based on vertex group prefixes

### 8. ArmatureXXMI Panel
- Displays the weight paint matching properties and offers buttons to execute the operations described above.

## Basic Logic

1. **Vertex Group Matching**:
   - Processes the base and target collections, filtering and merging meshes as necessary.
   - Calculates the weighted centers of vertex groups based on weight paint and vertex influence area.
   - Matches the vertex groups of the target object to the base object based on the proximity of the weighted centers.
   - Renames the armature bones according to the found matches.

2. **Armature Mirroring**:
   - Selects the armature and applies the mirror transformation along the global X-axis.

3. **Set Armature for Character**:
   - Renames armature bones as necessary to prepare the armature for the character.

4. **Set Character for Armature**:
   - Adds prefixes to the vertex groups of the objects in the base collection to ensure they correctly match the armature bones.

5. **Clean Armature**:
   - Removes bones from the armature that are not linked to any vertex groups.

6. **Split Mesh by Vertex Groups**
   - Identifies all identical prefixes Vertex Groups and splits the mesh based on them, then cleans up the empty vertex groups.


## Author

- **Gustav0_**

## Acknowledgements

- Main matching logic adapted from Comilarex: https://gamebanana.com/tools/15699
