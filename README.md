
SerenKit
========

SerenKit is a Blender add-on that provides tools for exporting and preparing models and modpacks for FFXIV. It includes export helpers, Material and Attribute management and automatic batch export for custom bodies.

**Quick Start**
- **Install:** Open Blender Preferences → Add-ons → Install..., choose this repository or copy the folder into your Blender add-ons directory.
- **Enable:** Enable the add-on in Preferences. Tested with Blender 5.0.
- **Textools Path:** Set the path to Textools in the add-on preferences (required for some export features).

**Features**
- **Export pipelines:** FBX/MDL export, preprocessing with robust weight transfer and unwraps.
- **Modpack support:** Tools for updating modpacks with exported models.
- **Shapekey utilities:** Helpers to manage shapekeys exports.
- **Materials and Attributes:** Support for setting materials and attributes from inside blender.

**Known Issues**
- Errors during export might leave the export header in the viewport.
- Missing proper error message when game path is incorrect.
- During export a copy of all exported objects is created, updating modifier references to the copy, but not updating drivers.
- Unwrap assumes that UV island borders are pinned.
- No checks if robust weight transfer is enabled.
- Currently code is very messy.
- Exporting is very slow.
- MDL conversion is done by creating a database file, in the future this should be done directly with Textools and add attributes and materials to the mdl file manually, to allow for threaded export.
