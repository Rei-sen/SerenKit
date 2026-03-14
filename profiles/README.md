Body Profiles — Usage Guide
===========================

Purpose
-------

This guide explains how SerenKit uses "profiles" to describe body-specific export settings (materials, shapekey groups, aliases, and incompatibilities) and how to create or fix a missing profile.

Where profiles live
-------------------

- Profiles are TOML files stored in the `profiles/` directory inside the add-on package.
- Profiles are loaded at add-on registration. You can reload them without restarting Blender via the Add-on Preferences: "Open Profiles Folder" → edit/add TOML → "Reload Profiles".
- The exporter UI shows loaded profiles in the "Export Profile" dropdown.

What to do if a profile is missing
---------------------------------

1. Open the profiles folder from Blender Preferences (Add-on Preferences → "Open Profiles Folder").
2. Copy `template.toml` to a new file (e.g. `mybody.toml`) and edit it.
3. Set `profile_name` to the display name you want to appear in the exporter dropdown.
4. Adjust `standard_materials`, `groups`, `export_aliases`, and `incompatibilities` as needed (see examples below).
5. Save the file and click "Reload Profiles" in the Add-on Preferences (or restart Blender).
6. Select the new profile in the exporter UI and proceed with export.

TOML structure (minimal example)
--------------------------------

profile_name = "MyBodyProfile"

[standard_materials]
"Base" = "/mt_base.mtrl"

[[groups]]
group_name = "Top"
mode = "exclusive"  # either "exclusive" or "optional"
[groups.shapekeys]
"Chest Large" = "Large"
"Chest Small" = "Small"

[export_aliases]
"AltName" = "RealName"

[incompatibilities]
Tummy = ["Legs Large", "Legs Medium"]

Key fields explained
--------------------

- `profile_name` — The visible name used in the exporter dropdown. This value (not the filename) is how SerenKit identifies the profile.
- `standard_materials` — Mapping of friendly material names to `.mtrl` paths used as suggestions while editing collection's materials.
- `groups` — An array of groups used to build variant combos:
  - `group_name` — Human name for the group (e.g., "Top", "Bottom").
  - `mode` — Either `exclusive` (pick at most one option) or `optional` (each option may be toggled independently).
  - `shapekeys` — Mapping of Blender shapekey names => export option names.
- `export_aliases` — Simple name remapping used by exporters.
- `incompatibilities` — Map a shapekey name to a list of other shapekey names that cannot be combined together.

Tips and troubleshooting
------------------------

- Unique `profile_name`: Make sure `profile_name` is unique across all TOML files to avoid collisions in the dropdown.
- Filename doesn't matter: The TOML filename can be anything; the `profile_name` field is authoritative.
- Syntax errors: Invalid TOML will be skipped during loading. Use the provided `template.toml` as a starting point.
- Quick checks: If the exporter dropdown shows "No Profiles Loaded", open the profiles folder and ensure valid `.toml` files exist.
- Programmatic reload: Use the Add-on Preferences button "Reload Profiles" to pick up new or changed TOML files without restarting Blender.

Helpful files
-------------

- Profile loading and validation: [shared/profile.py](../shared/profile.py)
- Example template: [profiles/template.toml](template.toml)
- Export UI / where the profile is picked: [operators/ffxiv_exporter.py](../operators/ffxiv_exporter.py)
- Variant generation logic: [shared/variants.py](../shared/variants.py)

# Place variant profile TOML files in this directory
# They will be loaded automatically when the addon initializes
